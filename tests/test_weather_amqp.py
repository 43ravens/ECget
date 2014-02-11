"""Unit tests for ECget weather_amqp module.

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
try:
    import unittest.mock as mock
except ImportError:     # pragma: no cover; happens for Python < 3.3
    import mock

import kombu.exceptions
import pytest


@pytest.fixture
def consumer():
    import ecget.weather_amqp
    consumer = ecget.weather_amqp.DatamartConsumer(
        queue_name='queue',
        routing_key='key',
        msg_handler=mock.Mock(),
    )
    consumer.exchange = mock.Mock(name='Exchange')
    consumer.queue = mock.Mock(
        name='Queue',
        return_value=mock.Mock(name='queue'),
    )
    return consumer


@pytest.fixture
def get_queue_name():
    import ecget.weather_amqp
    return ecget.weather_amqp.get_queue_name


@pytest.mark.usefixture('consumer')
class TestDatamartConsumer(object):
    @mock.patch('ecget.weather_amqp.time.time', return_value=1)
    def test_on_consume_ready_calcs_end_time(self, mock_time, consumer):
        consumer.lifetime = 1
        consumer.on_consume_ready(mock.Mock(), mock.Mock(), [])
        assert consumer.end_time == 2

    @pytest.mark.parametrize(
        'end_time, should_stop',
        [
            (2, True),
            (4, False),
        ]
    )
    @mock.patch('ecget.weather_amqp.time.time', return_value=3)
    def test_on_iteration(self, mock_time, consumer, end_time, should_stop):
        consumer.end_time = end_time
        consumer.on_iteration()
        assert consumer.should_stop is should_stop

    def test_get_consumers_binds_exchange_to_channel(self, consumer):
        mock_Consumer = mock.Mock(name='Consumer')
        mock_channel = mock.Mock(name='channel')
        consumer.get_consumers(mock_Consumer, mock_channel)
        consumer.exchange.assert_called_once_with(mock_channel)

    def test_get_consumers_binds_queue_to_channel(self, consumer):
        mock_Consumer = mock.Mock(name='Consumer')
        mock_channel = mock.Mock(name='channel')
        consumer.get_consumers(mock_Consumer, mock_channel)
        consumer.queue.assert_called_once_with(mock_channel)

    def test_get_consumers_checks_for_queue_on_server(self, consumer):
        mock_Consumer = mock.Mock(name='Consumer')
        mock_channel = mock.Mock(name='channel')
        consumer.get_consumers(mock_Consumer, mock_channel)
        consumer.queue().queue_declare.assert_called_once_with(passive=True)

    def test_get_consumers_declares_queue_on_server(self, consumer):
        mock_Consumer = mock.Mock(name='Consumer')
        mock_channel = mock.Mock(name='channel')
        consumer.queue().queue_declare.side_effect = [
            # Checking for queue raises channel error if queue doesn't exist
            kombu.exceptions.ChannelError,
            '',
        ]
        consumer.get_consumers(mock_Consumer, mock_channel)
        consumer.queue().queue_declare.assert_has_calls(
            [mock.call(passive=True), mock.call()]
        )

    def test_get_consumers_not_bind_existing_queue(self, consumer):
        mock_Consumer = mock.Mock(name='Consumer')
        mock_channel = mock.Mock(name='channel')
        consumer.queue().queue_declare.side_effect = [
            # Checking for queue raises channel error if queue doesn't exist
            kombu.exceptions.ChannelError,
            '',
        ]
        consumer.get_consumers(mock_Consumer, mock_channel)
        consumer.queue().queue_bind.assert_called_once_with()

    def test_get_consumers_binds_queue_on_server(self, consumer):
        mock_Consumer = mock.Mock(name='Consumer')
        mock_channel = mock.Mock(name='channel')
        consumer.get_consumers(mock_Consumer, mock_channel)
        assert not consumer.queue().queue_bind.called

    def test_get_consumers_returns_consumer_in_list(self, consumer):
        mock_Consumer = mock.Mock(name='Consumer')
        mock_channel = mock.Mock(name='channel')
        result = consumer.get_consumers(mock_Consumer, mock_channel)
        expected = [
            mock_Consumer(
                queues=consumer.queue(),
                callbacks=[consumer.msg_handler],
                auto_declare=False,
            )
        ]
        assert result == expected

    def test_handle_msg_calls_msg_handler(self, consumer):
        mock_body = mock.Mock(name='body')
        consumer.handle_msg(mock_body, mock.Mock(name='msg'))
        consumer.msg_handler.assert_called_once_with(mock_body)

    def test_handle_msg_acknowledges_msg(self, consumer):
        mock_msg = mock.Mock(name='msg')
        consumer.handle_msg(mock.Mock(name='body'), mock_msg)
        mock_msg.ack.assert_called_once_with()


def test_get_queue_name_creates_queues_dir(get_queue_name):
    with mock.patch('ecget.weather_amqp.os.path.exists', return_value=False):
        with mock.patch('ecget.weather_amqp.os.mkdir') as mock_mkdir:
            get_queue_name('foo')
    mock_mkdir.assert_called_once_with('./queues')


def test_get_queue_name_creates_queue_file(get_queue_name):
    m_open = mock.mock_open()
    with mock.patch('ecget.weather_amqp.os.path.exists', return_value=False):
        with mock.patch('ecget.weather_amqp.os.mkdir'):
            with mock.patch('ecget.weather_amqp.open', m_open, create=True):
                get_queue_name('foo')
    m_open.assert_called_once_with('./queues/foo', 'wt')


@mock.patch('ecget.weather_amqp.uuid.uuid4', return_value='uuid')
def test_get_queue_name_writes_queue_name_to_file(mock_uuid4, get_queue_name):
    m_open = mock.mock_open()
    with mock.patch('ecget.weather_amqp.os.path.exists', return_value=False):
        with mock.patch('ecget.weather_amqp.os.mkdir'):
            with mock.patch('ecget.weather_amqp.open', m_open, create=True):
                get_queue_name('foo')
    m_open().write.assert_called_once_with('foo.uuid')


def test_get_queue_name_returns_queue_name_from_file(get_queue_name):
    with mock.patch('ecget.weather_amqp.os.path.exists', return_value=True):
        patch_open = mock.patch(
            'ecget.weather_amqp.open',
            mock.mock_open(read_data='foo.uuid'),
            create=True,
        )
        with patch_open:
            queue_name = get_queue_name('foo')
    assert queue_name == 'foo.uuid'
