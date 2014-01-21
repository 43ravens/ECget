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
import cliff.command
import requests
import stevedore.driver


class RiverFlow(cliff.command.Command):
    """Get EC river flow data and output daily average value(s) for SOG.
    """
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        read_mgr = stevedore.driver.DriverManager(
            namespace='ecget.get_data',
            name='river.discharge',
            invoke_on_load=True,
        )
        read_mgr.driver.get_data(
            '08MF005', arrow.get(2014, 1, 1), arrow.get(2014, 1, 1))


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

        :returns:
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

        :returns:
        """
        last_date = end_date.replace(days=1)
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
        self.log.info(response.text)
