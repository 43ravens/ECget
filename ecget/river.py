# Copyright 2014 Doug Latornell and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ECget command plug-in to get river flow data and output daily average
value(s) for SOG.
"""
import datetime
import logging
import sys
import warnings

import arrow
import bs4
import cliff.command
import requests
import stevedore.driver


__all__ = [
    'RiverFlow', 'RiverDataBase', 'RiverDischarge',
]


class RiverFlow(cliff.command.Command):
    """Get EC river flow data and output daily average value(s) for SOG.

    ECget command plug-in.
    """
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(RiverFlow, self).get_parser(prog_name)
        parser.description = (
            'Get EC river flow data and output daily average value(s) for SOG.'
        )
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
            help='last date to get data for; YYYY-MM-DD. '
                 'Defaults to start date.',
        )
        parser.add_argument(
            '--no-verify-ssl-certs',
            dest='verify_ssl_certs',
            action='store_false',
            help="Don't verify SSL certificates chain for requests to "
                 "https://wateroffice.ec.gc.ca/. "
                 "Also suppress InsecureRequestWarning warnings from urllib3 vendored in the "
                 "requests package. "
                 "This is a hack to reduce the noise from cron jobs on some systems that have "
                 "problems with the Nov-2018 forced redirection to https://wateroffice.ec.gc.ca/."
                 "Defaults to False.",
        )
        return parser

    def take_action(self, parsed_args):
        if parsed_args.end_date is None:
            parsed_args.end_date = parsed_args.start_date
        raw_data = self._get_data(
            parsed_args.station_id,
            parsed_args.start_date,
            parsed_args.end_date,
            parsed_args.verify_ssl_certs,
        )
        daily_avgs = self._calc_daily_avgs(raw_data, parsed_args.end_date)
        if len(daily_avgs) > 1:
            self._interpolate_missing(daily_avgs)
        self._output_results(daily_avgs)

    def _get_data(self, station_id, start_date, end_date, verify_ssl_certs):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.get_data',
            name='river.discharge',
            invoke_on_load=True,
        )
        raw_data = mgr.driver.get_data(station_id, start_date, end_date, verify_ssl_certs)
        msg = ('got {} river discharge data for {}'
               .format(station_id,
                       start_date.format('YYYY-MM-DD')))
        if start_date != end_date:
            msg += ' to {}'.format(end_date.format('YYYY-MM-DD'))
        self.log.debug(msg)
        return raw_data

    def _calc_daily_avgs(self, raw_data, end_date):
        tds = raw_data.findAll('td')
        timestamps = (td.string for td in tds[::3])
        flows = (td.text for td in tds[1::3])
        data_day = self._read_datestamp(tds[0].string)
        flow_sum = count = 0
        daily_avgs = []
        msg = (
            'calculated average flow for {data_day} from {count} observations')
        for timestamp, flow in zip(timestamps, flows):
            datestamp = self._read_datestamp(timestamp)
            if datestamp > end_date:
                break
            if datestamp == data_day:
                flow_sum += self._convert_flow(flow)
                count += 1
            else:
                daily_avgs.append((data_day, flow_sum / count))
                self.log.debug(msg.format(data_day=data_day, count=count))
                data_day = datestamp
                flow_sum = self._convert_flow(flow)
                count = 1
        daily_avgs.append((data_day, flow_sum / count))
        self.log.debug(msg.format(data_day=data_day, count=count))
        return daily_avgs

    def _read_datestamp(self, string):
        return (arrow.get(string, 'YYYY-MM-DD HH:mm:ss')
                .replace(hour=0, minute=0, second=0))

    def _convert_flow(self, flow_string):
        """Convert a flow data value from a string to a float.

        Handles 'provisional values' which are marked with a `*` at
        the end of the string.
        """
        try:
            return float(flow_string.replace(',', ''))
        except ValueError:
            # Ignore training `*`
            return float(flow_string.replace(',', '')[:-1])

    def _interpolate_missing(self, daily_avgs):
        """Fill in any missing data values by linear interpolation.
        """
        i = 0
        while True:
            try:
                delta = (daily_avgs[i + 1][0] - daily_avgs[i][0]).days
            except IndexError:
                break
            if delta > 1:
                gap_start = i + 1
                for j in range(1, delta):
                    missing_date = (
                        daily_avgs[i][0]
                        + j * datetime.timedelta(days=1))
                    daily_avgs.insert(i + j, (missing_date, None))
                    self.log.debug(
                        'interpolated average flow for {date}'
                        .format(date=missing_date.format('YYYY-MM-DD')))
                gap_end = i + delta - 1
                self._interpolate_values(daily_avgs, gap_start, gap_end)
            i += delta

    def _interpolate_values(self, daily_avgs, gap_start, gap_end):
        """Calculate missing data values by linear interpolation.
        """
        last_value = daily_avgs[gap_start - 1][1]
        next_value = daily_avgs[gap_end + 1][1]
        delta = (next_value - last_value) / (gap_end - gap_start + 2)
        for i in range(gap_end - gap_start + 1):
            datestamp = daily_avgs[gap_start + i][0]
            value = last_value + delta * (i + 1)
            daily_avgs[gap_start + i] = (datestamp, value)

    def _output_results(self, daily_avgs):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.formatter',
            name='SOG.river.daily_avg_flow',
            invoke_on_load=True,
        )
        for chunk in mgr.driver.format(daily_avgs):
            sys.stdout.write(chunk)


class RiverDataBase(object):
    """Base class for EC river data site drivers.
    """
    DATA_URL = 'https://wateroffice.ec.gc.ca/report/real_time_e.html'
    DISCLAIMER_COOKIE = {'disclaimer': 'agree'}
    PARAM_IDS = {
        'discharge': 47,
        'water level': 46,
        'water temperature': 5,
    }

    def __init__(self, param):
        self.params = {
            'mode': 'Table',
            'type': 'realTime',
            'prm1': self.PARAM_IDS[param],
            'prm2': self.PARAM_IDS['water level'],
        }

    def get_data(self, station_id, start_date, end_date, verify_ssl_certs):
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
            'startDate': start_date.format('YYYY-MM-DD'),
            'endDate': last_date.format('YYYY-MM-DD'),
        })
        if not verify_ssl_certs:
            if not sys.warnoptions:
                warnings.simplefilter("ignore")
        response = requests.get(
            self.DATA_URL, params=self.params, cookies=self.DISCLAIMER_COOKIE, verify=verify_ssl_certs)
        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        return soup.find('table')


class RiverDischarge(RiverDataBase):
    """ECget driver to get river discharge data from Environment Canada
    wateroffice.ec.gc.ca site.
    """
    def __init__(self):
        super(RiverDischarge, self).__init__('discharge')
