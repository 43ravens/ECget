"""ECget driver plug-in to get weather data from CMC Datamart URLs.

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

import requests
import xml.etree.ElementTree as ET


class DatamartWeatherBase(object):
    """Base class for driver plug-in to get weather data from an
    Environment Canada CMC Datamart URL.

    :arg url: URL to get SWOB-ML data file from.
    :type url: str
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, url):
        self.url = url

    def filter(self, criterion):
        """Check URL against criterion to ensure that only URLs for data
        of interest are processed.

        :arg criterion:
        :type criterion:

        :returns: URL or :py:obj:`None`
        """

    def get_data(self, *labels):
        """Get the SWOB-ML data for the specified labels.

        :arg *labels: List of SWOB-ML label strings to get data for.

        :returns: Dictionary of SWOB-ML attributes and values found for
                  each label.
                  The dictionary keys the the requested labels,
                  and the values are dicts of the attributes and their
                  values.
        """


class DatamartWeather(DatamartWeatherBase):
    """Driver plug-in to get weather data from an Environment Canada
    CMC Datamart URL.

    :arg url: URL to get SWOB-ML data file from.
    :type url: str
    """
    PT_OBS_NS = '{http://dms.ec.gc.ca/schema/point-observation/2.0}'
    ID_ELEMENTS_TAG = ''.join((PT_OBS_NS, 'identification-elements'))
    ELEMENTS_TAG = ''.join((PT_OBS_NS, 'elements'))

    log = logging.getLogger(__name__)

    def filter(self, criterion):
        """
        """
        pass

    def get_data(self, *labels):
        """Get the SWOB-ML data for the specified labels.

        :arg *labels: List of SWOB-ML label strings to get data for.

        :returns: Dictionary of SWOB-ML attributes and values found for
                  each label.
                  The dictionary keys the the requested labels,
                  and the values are dicts of the attributes and their
                  values.
        """
        def interesting(elements):
            for el in elements:
                if el.attrib['name'] in labels:
                    yield el.attrib.pop('name'), el.attrib

        def get_timestep(id_elements):
            for el in id_elements:
                if el.attrib['name'] == 'date_tm':
                    return el.attrib['value']
        data = {}
        response = requests.get(self.url)
        root = ET.fromstring(response.content)
        try:
            id_elements = list(root.iter(self.ID_ELEMENTS_TAG))[0]
        except IndexError:
            self.log.warn(
                'no {0.ID_ELEMENTS_TAG} tag found in {0.url}'.format(self))
            return data
        try:
            elements = list(root.iter(self.ELEMENTS_TAG))[0]
        except IndexError:
            self.log.warn(
                'no {0.ELEMENTS_TAG} tag found in {0.url}'.format(self))
            return data
        for name, attrs in interesting(elements):
            data.update({name: attrs})
        if data:
            data['timestamp'] = get_timestep(id_elements)
        return data
