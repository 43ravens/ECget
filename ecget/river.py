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
        read_mgr.driver.get_data()


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
    def get_data(self):
        """
        """


class RiverDischarge(RiverDataBase):
    """ECget driver to get river discharge data from Environment Canada
    wateroffice.ec.gc.ca site.
    """
    log = logging.getLogger(__name__)

    def __init__(self):
        super(RiverDischarge, self).__init__('discharge')

    def get_data(self):
        self.params.update({
            'stn': '08MF005',
            'syr': 2014,
            'smo': 1,
            'sday': 1,
            'eyr': 2014,
            'emo': 1,
            'eday': 2,
        })
        with requests.session() as s:
            s.post(self.DISCLAIMER_URL, data=self.DISCLAIMER_ACTION)
            time.sleep(2)
            response = s.get(self.DATA_URL, params=self.params)
        self.log.debug('got river data')
        self.log.info(response.text)
