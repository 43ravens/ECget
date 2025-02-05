# Copyright 2014-2017 Doug Latornell and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""ECget command plug-in to get EC Fraser River water quality buoy data and
output them as a CSV file line.
"""
import logging
import sys
from types import SimpleNamespace

import arrow
import bs4
import cliff.command
from dateutil import tz
import requests
import stevedore.driver


class FraserWaterQuality(cliff.command.Command):
    """Get EC Fraser River water quality buoy data and output them as a CSV
    file line.

    ECget command plug-in.
    """
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(FraserWaterQuality, self).get_parser(prog_name)
        parser.description = (
            'Get EC Fraser River water quality buoy data and output them as a '
            'CSV file line.')
        return parser

    def take_action(self, parsed_args):
        data = self._get_data()
        self._output_results(data)

    def _get_data(self):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.get_data',
            name='fraser.water_quality',
            invoke_on_load=True, )
        data_soup = mgr.driver.get_data()
        data = SimpleNamespace()
        last_update_time = arrow.get(
            data_soup.find('span', {'id': 'mainContentTime_LastUpdateTime'}).text)
        data.last_update_time = arrow.get(last_update_time.datetime,
                                          tz.gettz('Canada/Pacific'))
        self.log.debug(
            'got Fraser River water quality data recorded {}'.format(
                data.last_update_time.format("YYYY-MM-DD HH:mm:ss ZZ")))
        scalar_data = {
            'turbidity': 'MainContent_turbidty',
            'specific_conductivity': 'MainContent_specCond',
            'water_temperature': 'MainContent_waterTemp',
            'dissolved_oxygen': 'MainContent_DOper',
            'water_depth': 'MainContent_waterDepth',
            'wind_speed': 'MainContent_windSpeed',
            'air_temperature': 'MainContent_airTemp',
            'relative_humidity': 'MainContent_relHumid',
            'atm_pressure': 'MainContent_pressure',
        }
        for qty, id in scalar_data.items():
            try:
                value, units = self._parse_scalar(data_soup, id)
                setattr(data, qty, value)
                setattr(data, '{}_units'.format(qty), units)
            except ValueError:
                # No data value or units
                ignore_instrument_warnings = {'wind_speed', 'water_depth'}
                if qty not in ignore_instrument_warnings:
                    # Suppress email warnings from instruments that we don't care about:
                    #   * Anemometer stopped reporting for a while in Dec-2018
                    #   * Water depth stopped reporting for a while in Nov-2022
                    logging.warning(
                        'invalid {0} data: {1}'
                        .format(qty, data_soup.find('span', {'id': id})
                        .parent.text))
                setattr(data, qty, 'n/a')
                setattr(data, '{}_units'.format(qty), 'n/a')
            self.log.debug('{0}: {1} {2}'.format(qty, value, units))
        data.pH = float(data_soup.find('span', {'id': 'MainContent_pH'}).text)
        data.pH_scale = 'NIST'
        self.log.debug('pH: {0.pH} {0.pH_scale}'.format(data))
        parts = data_soup.find(
            'span', {'id': 'MainContent_waterVelocity'}).text.split()
        try:
            data.stream_velocity = float(parts[0])
            data.stream_velocity_units = parts[1]
            data.stream_velocity_direction = ' '.join(parts[2:]).lower()
        except IndexError:
            # No stream velocity data
            data.stream_velocity, data.stream_velocity_units = 'n/a', 'n/a'
            data.stream_velocity_direction = 'n/a'
        self.log.debug(
            'stream_velocity: {0.stream_velocity} {0.stream_velocity_units} '
            '{0.stream_velocity_direction}'.format(data))
        parts = data_soup.find(
            'span', {'id': 'MainContent_windDirection'}).text.split()
        try:
            data.wind_direction = ' '.join(parts[:2]).lower()
            data.wind_bearing = parts[-1].replace('(', '').replace(')', '')
        except IndexError:
            # No wind direction data
            data.wind_direction, data.wind_bearing = 'n/a', 'n/a'
        self.log.debug(
            'wind_direction: {0.wind_direction} {0.wind_bearing}'.format(data))
        return data

    def _output_results(self, data):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.formatter',
            name='fraser.water_quality.csv',
            invoke_on_load=True, )
        csv_line = mgr.driver.format(data)
        sys.stdout.write(csv_line)

    def _parse_scalar(self, data_soup, data_id):
        value, units = data_soup.find(
            'span', {'id': data_id}).parent.text.split()
        return float(value), units


class FraserWaterQualityData:
    """ECget driver to get Fraser River water quality buoy data from
    Environment Canada https://aquatic.pyr.ec.gc.ca/realtimebuoys/default.aspx
    page.
    """
    DATA_URL = 'https://aquatic.pyr.ec.gc.ca/realtimebuoys/default.aspx'

    def get_data(self):
        """Get Fraser River water quality buoy data from Environment Canada
        https://aquatic.pyr.ec.gc.ca/realtimebuoys/default.aspx page.

        :returns: BeautifulSoup parser object containing data table
                  from EC page.
        """
        response = requests.get(self.DATA_URL)
        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        return soup


class FraserWaterQualityCSV:
    """Format Fraser River water quality buoy data from Environment Canada
    https://aquatic.pyr.ec.gc.ca/realtimebuoys/default.aspx page as a line
    to go into a CSV file.
    """

    def format(self, data):
        """Format the data as a CSV file line.

        :arg data: Fraser River water quality buoy data namespace object.

        :returns: CSV line.
        :rtype: str
        """
        csv_line = ('{date},{time},{timezone}'.format(
            date=data.last_update_time.format('YYYY-MM-DD'),
            time=data.last_update_time.format('HH:mm:ss'),
            timezone=data.last_update_time.tzinfo.tzname(
                data.last_update_time.datetime), ))
        qtys = ('turbidity', 'specific_conductivity', 'water_temperature')
        for qty in qtys:
            csv_line = ','.join((csv_line, str(getattr(data, qty)), getattr(
                data, '{}_units'.format(qty))))
        csv_line = ','.join((csv_line, str(data.pH), data.pH_scale))
        qtys = ('dissolved_oxygen', 'water_depth', 'stream_velocity')
        for qty in qtys:
            csv_line = ','.join((csv_line, str(getattr(data, qty)), getattr(
                data, '{}_units'.format(qty))))
        csv_line = ','.join((csv_line, data.stream_velocity_direction))
        csv_line = ','.join(
            (csv_line, str(data.wind_speed), data.wind_speed_units,
             data.wind_direction, data.wind_bearing))
        qtys = ('air_temperature', 'relative_humidity', 'atm_pressure')
        for qty in qtys:
            csv_line = ','.join((csv_line, str(getattr(data, qty)), getattr(
                data, '{}_units'.format(qty))))
        csv_line += '\n'
        return csv_line
