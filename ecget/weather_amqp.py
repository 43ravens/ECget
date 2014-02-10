"""Consumer for EC CMC Datamart AMQP topic exchange service.

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
import os
import time
import uuid

import kombu
import kombu.exceptions
import kombu.mixins


__all__ = [
    'DatamartConsumer', 'get_queue_name',
]


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
    CONNECTION = {
        'transport': 'amqp',
        'userid': 'anonymous',
        'password': 'anonymous',
        'hostname': 'dd.weather.gc.ca',
        'port': 5672,
        'virtual_host': '/',
    }
    EXCHANGE = {
        'name': 'xpublic',
        'type': 'topic',
    }

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
        """Close the connection to the server.
        """
        connection.close()

    def get_consumers(self, Consumer, channel):
        """Bind exchange and queue to AMQP channel.
        If the queue does not exits on the server,
        declare it to the server and bind it to the exchange and routing key.

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
        self.connection = kombu.Connection(**self.CONNECTION)
        self.exchange = kombu.Exchange(**self.EXCHANGE)
        self.queue = kombu.Queue(
            name=self.queue_name,
            exchange=self.exchange,
            routing_key=self.routing_key,
        )
        if self.queue_expiry is not None:
            self.queue.queue_arguments = {'x-expires': self.queue_expiry}
        super(DatamartConsumer, self).run()


def get_queue_name(prefix):
    """Return a queue name based on the prefix.

    The queue name is the prefix with the string representation of a
    random UUID dot-appended to it;
    i.e. the queue name for the prefix :kbd:`foo.bar` might be
    :kbd:`foo.bar.4749cb1b-b33d-46ac-b89c-b4d469ddabe9`.

    Queues persist on the AMQP server but the name can only be provided
    by the client/consumer.
    To allow the client/consumer to re-connect to a queue that it has
    already created on the server,
    queue names are stored in the :file:`./queues/` directory in files
    named with their prefixes.

    If a queue file with the name prefix exists in the :file:`./queues/`
    directory its contents are returned as the queue name.
    Otherwise,
    a random UUID is dot-appended to prefix,
    stored in a file called prefix in the :file:`./queues/` directory,
    and the newly created queue name is returned.

    This function creates the :file:`./queues/` directory if it does not
    already exist.

    :arg prefix: Queue name prefix.
    :type prefix: str

    :returns: Queue name
    :rtype: str
    """
    queues_dir = os.path.join('.', 'queues')
    if not os.path.exists(queues_dir):
        os.mkdir(queues_dir)
    queue_file = os.path.join(queues_dir, prefix)
    if not os.path.exists(queue_file):
        queue_name = '.'.join((prefix, str(uuid.uuid4())))
        with open(queue_file, 'wt') as f:
            f.write(queue_name)
    else:
        with open(queue_file, 'rt') as f:
            queue_name = f.read()
    return queue_name
