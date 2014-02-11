"""ECget command plug-ins to get weather data via Datamrt AMQP service
and output hourly value(s) for SOG.

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
import logging
import math
import sys

import arrow
import cliff
import stevedore.driver

from . import weather_amqp


__all__ = [
    'SOGWeatherCommandBase',
    'SandHeadsWind',
]


class SOGWeatherCommandBase(cliff.command.Command):
    """Base class for SOG weather command plug-ins.

    Sub-classes are expected to provide:

    * :attr:`QUEUE_NAME_PREFIX` class attribute that is the prefix part
      of the AMQP queue name

    * :attr:`ROUTING_KEY` class attribute that is the routing key for
       the AMQP queue

    * :meth:`handle_msg` instance method that accepts the AMQP message
      as an argument and processes it to emit a timestamped weather data
      value formatted for SOG
    """
    QUEUE_NAME_PREFIX = None
    ROUTING_KEY = None

    def get_parser(self, prog_name):
        parser = super(SOGWeatherCommandBase, self).get_parser(prog_name)
        parser.add_argument(
            '--lifetime',
            type=int,
            default=900,
            help='queue consumer lifetime in seconds; defaults to 900',
        )
        return parser

    def take_action(self, parsed_args):
        queue_name = weather_amqp.get_queue_name(self.QUEUE_NAME_PREFIX)
        consumer = weather_amqp.DatamartConsumer(
            queue_name=queue_name,
            routing_key=self.ROUTING_KEY,
            msg_handler=self.handle_msg,
            lifetime=parsed_args.lifetime,
        )
        consumer.run()

    def output_results(self, data):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.formatter',
            name='weather.hourly',
            invoke_on_load=True,
        )
        for chunk in mgr.driver.format(data):
            sys.stdout.write(chunk)

    def handle_msg(self, body):
        raise NotImplemented


class SandHeadsWind(SOGWeatherCommandBase):
    """Get Sand Heads wind data via AMQP and output hourly component values for SOG.

    ECget command plug-in.
    """
    QUEUE_NAME_PREFIX = 'cmc.SoG.SandHeads'
    ROUTING_KEY = 'exp.dd.notify.observations.swob-ml.*.CWVF'

    STRAIT_HEADING = math.radians(305)

    log = logging.getLogger(__name__)

    def handle_msg(self, body):
        self.log.debug(body)
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.get_data',
            name='wind',
            invoke_on_load=True,
            invoke_args=(body,),
        )
        raw_data = mgr.driver.get_data(
            'avg_wnd_spd_10m_mt58-60', 'avg_wnd_dir_10m_mt58-60')
        hourly_winds = self._calc_hourly_winds(raw_data)
        self.output_results(hourly_winds)

    def _calc_hourly_winds(self, raw_data):
        timestamp = arrow.get(raw_data['timestamp']).to('PST')
        speed = float(raw_data['avg_wnd_spd_10m_mt58-60']['value'])
        direction = float(raw_data['avg_wnd_dir_10m_mt58-60']['value'])
        # Convert speed from km/hr to m/s
        speed = speed * 1000 / (60 * 60)
        # Convert wind speed and direction to u and v components
        radian_direction = math.radians(direction)
        u_wind = speed * math.sin(radian_direction)
        v_wind = speed * math.cos(radian_direction)
        # Rotate components to align u direction with Strait
        cross_wind = (
            u_wind * math.cos(self.STRAIT_HEADING)
            - v_wind * math.sin(self.STRAIT_HEADING)
        )
        along_wind = (
            u_wind * math.sin(self.STRAIT_HEADING)
            + v_wind * math.cos(self.STRAIT_HEADING)
        )
        # Resolve atmosphere/ocean direction convention difference in
        # favour of oceanography
        cross_wind = -cross_wind
        along_wind = -along_wind
        return [(timestamp, (cross_wind, along_wind))]

    def output_results(self, hourly_winds):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.formatter',
            name='wind.hourly.components',
            invoke_on_load=True,
        )
        for chunk in mgr.driver.format(hourly_winds):
            sys.stdout.write(chunk)
