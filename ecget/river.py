"""ECget command plug-in to get river flow data and output daily average
value(s) for SOG.

Copyright 2014 Doug Latornell and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import abc
import logging
import time

import arrow
import bs4
import cliff.command
import requests
import stevedore.driver


class RiverFlow(cliff.command.Command):
    """Get EC river flow data and output daily average value(s) for SOG.
    """
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(RiverFlow, self).get_parser(prog_name)
        parser.add_argument(
            'station_id',
            help=('EC station id of river to get data for; '
                  'see http://www.wateroffice.ec.gc.ca/text_search/'
                  'search_e.html.'),
        )
        parser.add_argument(
            'start_date',
            type=arrow.get,
            help='first date to get data for; YYYY-MM-DD',
        )
        parser.add_argument(
            '-e', '--end-date',
            type=arrow.get,
            help='last date to get data for; YYYY-MM-DD.'
                 'Defaults to start date.',
        )
        return parser

    def take_action(self, parsed_args):
        if parsed_args.end_date is None:
            parsed_args.end_date = parsed_args.start_date
        raw_data = self._get_data(
            parsed_args.station_id,
            parsed_args.start_date,
            parsed_args.end_date,
        )
        daily_avgs = self._process_data(raw_data, parsed_args.end_date)
        self._output_results(daily_avgs)

    def _get_data(self, station_id, start_date, end_date):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.get_data',
            name='river.discharge',
            invoke_on_load=True,
        )
        raw_data = mgr.driver.get_data(station_id, start_date, end_date)
        msg = ('got {} river discharge data for {}'
               .format(station_id,
                       start_date.format('YYYY-MM-DD')))
        if start_date != end_date:
            msg += ' to {}'.format(end_date.format('YYYY-MM-DD'))
        self.log.debug(msg)
        return raw_data

    def _process_data(self, raw_data, end_date):
        tds = raw_data.findAll('td')
        timestamps = (td.string for td in tds[::2])
        flows = (td.text for td in tds[1::2])
        data_day = self._read_datestamp(tds[0].string)
        flow_sum = count = 0
        daily_avgs = []
        for timestamp, flow in zip(timestamps, flows):
            datestamp = self._read_datestamp(timestamp)
            if datestamp > end_date.date():
                break
            if datestamp == data_day:
                flow_sum += self._convert_flow(flow)
                count += 1
            else:
                daily_avgs.append((data_day, flow_sum / count))
                data_day = datestamp
                flow_sum = self._convert_flow(flow)
                count = 1
        daily_avgs.append((data_day, flow_sum / count))
        return daily_avgs

    def _read_datestamp(self, string):
        return arrow.get(string, 'YYYY-MM-DD HH:mm:ss').date()

    def _convert_flow(self, flow_string):
        """Convert a flow data value from a string to a float.

        Handles 'provisional values' which are marked with a `*` at
        the end of the string.
        """
        try:
            return float(flow_string)
        except ValueError:
            # Ignore training `*`
            return float(flow_string[:-1])

    def _output_results(self, daily_avgs):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.formatter',
            name='river.daily_avg_flow',
            invoke_on_load=True,
        )
        for chunk in mgr.driver.format(daily_avgs):
            print(chunk, end='')


class RiverDataBase(object):
    """Base class for EC river data site drivers.
    """
    __metaclass__ = abc.ABCMeta

    DISCLAIMER_URL = 'http://www.wateroffice.ec.gc.ca/include/disclaimer.php'
    DISCLAIMER_ACTION = {'disclaimer_action': 'I Agree'}
    DATA_URL = 'http://www.wateroffice.ec.gc.ca/graph/graph_e.html'
    PARAM_IDS = {
        'discharge': 6,
    }

    def __init__(self, param):
        self.params = {
            'mode': 'text',
            'prm1': self.PARAM_IDS[param],
        }

    @abc.abstractmethod
    def get_data(self, station_id, start_date, end_date):
        """Get river data from the Environment Canada wateroffice.ec.gc.ca
        site.

        :arg station_id: Station id
                         - see http://www.wateroffice.ec.gc.ca/text_search/search_e.html.
        :type station_id: str

        :arg start_date: First date to get data for.
        :type start_date: :py:class:`arrow.Arrow` instance

        :arg end_date: Last date to get data for.
        :type end_date: :py:class:`arrow.Arrow` instance

        :returns: BeautifulSoup parser object containing data table
                  from EC page.
        """


class RiverDischarge(RiverDataBase):
    """ECget driver to get river discharge data from Environment Canada
    wateroffice.ec.gc.ca site.
    """
    log = logging.getLogger(__name__)

    def __init__(self):
        super(RiverDischarge, self).__init__('discharge')

    def get_data(self, station_id, start_date, end_date):
        """Get river data from the Environment Canada wateroffice.ec.gc.ca
        site.

        :arg station_id: Station id
                         - see http://www.wateroffice.ec.gc.ca/text_search/search_e.html.
        :type station_id: str

        :arg start_date: First date to get data for.
        :type start_date: :py:class:`arrow.Arrow` instance

        :arg end_date: Last date to get data for.
        :type end_date: :py:class:`arrow.Arrow` instance

        :returns: BeautifulSoup parser object containing data table
                  from EC page.
        """
        last_date = end_date.replace(days=+1)
        self.params.update({
            'stn': station_id,
            'syr': start_date.year,
            'smo': start_date.month,
            'sday': start_date.day,
            'eyr': last_date.year,
            'emo': last_date.month,
            'eday': last_date.day,
        })
        with requests.session() as s:
            s.post(self.DISCLAIMER_URL, data=self.DISCLAIMER_ACTION)
            time.sleep(2)
            response = s.get(self.DATA_URL, params=self.params)
        soup = bs4.BeautifulSoup(response.content)
        return soup.find('table', id='dataTable')
