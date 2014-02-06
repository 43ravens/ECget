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
import time

import arrow
import cliff
import kombu
import kombu.exceptions
import kombu.mixins
import stevedore.driver


class SandHeadsWind(cliff.command.Command):
    """Get Sand Heads wind data via AMQP and output hourly component
    values for SOG.

    ECget command plug-in.
    """
    STRAIT_HEADING = math.radians(305)

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SandHeadsWind, self).get_parser(prog_name)
        parser.description = (
            'Get Sand Heads wind data via AMQP and output hourly component '
            'values for SOG.'
        )
        parser.add_argument(
            '--lifetime',
            type=int,
            default=900,
            help='queue consumer lifetime in seconds; defaults to 900',
        )
        return parser

    def take_action(self, parsed_args):
        consumer = DatamartConsumer(
            queue_name='cmc.SoG.SandHeads',
            routing_key='exp.dd.notify.observations.swob-ml.*.CWVF',
            msg_handler=self._handle_msg,
            lifetime=parsed_args.lifetime,
        )
        consumer.run()

    def _handle_msg(self, body):
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
        self._output_results(hourly_winds)

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

    def _output_results(self, hourly_winds):
        mgr = stevedore.driver.DriverManager(
            namespace='ecget.formatter',
            name='wind.hourly.components',
            invoke_on_load=True,
        )
        for chunk in mgr.driver.format(hourly_winds):
            sys.stdout.write(chunk)


class DatamartConsumer(kombu.mixins.ConsumerMixin):
    """Consumer for EC CMC Datamart AMQP topic exchange service.

    :arg queue_name: Name of message queue to consume from.
    :type queue_name: str

    :arg routing_key: Routing key that the queue will receive.
                       Also known as exchange key or binding key.
    :type routing_key: str

    :arg msg_handler: Callable that will process body of messages received
                      on the queue.

    :arg lifetime: Number of seconds that the consumer should operate for.
                   Note that if the connection to the AMQP broker is lost
                   the consumer will attempt to re-establish for a new
                   lifetime period.
    :type lifetime: int

    :arg queue_expiry: Number of seconds to send to broker as value of
                       :kbd:`x-expires` queue declaration argument.
    :type queue_expiry: int
    """
    log = logging.getLogger(__name__)

    def __init__(
        self,
        queue_name,
        routing_key,
        msg_handler,
        lifetime=900,
        queue_expiry=None,
    ):
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.msg_handler = msg_handler
        self.lifetime = lifetime
        self.queue_expiry = queue_expiry

    def on_consume_ready(self, connection, channel, consumers, **kwargs):
        """Calculate when the consumer should shut itself down.
        """
        self.end_time = time.time() + self.lifetime
        self.log.debug(
            'consumer starting for {.lifetime} sec lifetime'.format(self))

    def on_iteration(self):
        """Check for consumer shut-down time.
        """
        if time.time() > self.end_time:
            self.log.debug('consumer lifetime limit reached')
            self.should_stop = True

    def on_consume_end(self, connection, channel):
        connection.close()

    def get_consumers(self, Consumer, channel):
        """Bind exchange and queue to AMQP channel,
        declare queue to the server and bind it to the exchange and
        routing key.

        :returns: List containing a configured Consumer instance.
        """
        exchg = self.exchange(channel)
        self.log.debug('exchange bound to channel: {}'.format(exchg))
        queue = self.queue(channel)
        self.log.debug('queue bound to channel: {}'.format(queue))
        try:
            queue.queue_declare(passive=True)
            self.log.debug('queue exists on server')
        except kombu.exceptions.ChannelError:
            queue.queue_declare()
            self.log.debug('queue declared on server')
            queue.queue_bind()
            self.log.debug('queue binding created on server')
        return [
            Consumer(
                queues=[queue],
                callbacks=[self.handle_msg],
                auto_declare=False,
            )
        ]

    def handle_msg(self, body, message):
        """Pass the body of a received message to the message handler
        and acknowledge receipt of the message to the server.
        """
        self.msg_handler(body)
        message.ack()

    def run(self):
        """Run the consumer.
        """
        self.connection = kombu.Connection(
            transport='amqp',
            hostname='dd.weather.gc.ca',
            port='5672',
            userid='anonymous',
            password='anonymous',
            virtual_host='/',
        )
        self.exchange = kombu.Exchange(name='xpublic', type='topic')
        self.queue = kombu.Queue(
            name=self.queue_name,
            exchange=self.exchange,
            routing_key=self.routing_key,
        )
        if self.queue_expiry is not None:
            self.queue.queue_arguments = {'x-expires': self.queue_expiry}
        super(DatamartConsumer, self).run()
