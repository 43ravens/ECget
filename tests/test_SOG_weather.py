"""Unit tests for ECget SOG_weather module.

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
import math
try:
    import unittest.mock as mock
except ImportError:     # pragma: no cover; happens for Python < 3.3
    import mock

import arrow
import cliff
import pytest


@pytest.fixture
def sh_wind():
    import ecget.SOG_weather
    return ecget.SOG_weather.SandHeadsWind(mock.Mock(spec=cliff.app.App), [])


@pytest.mark.usefixture('sh_wind')
class TestSandHeadsWind(object):
    def test_get_parser(self, sh_wind):
        parser = sh_wind.get_parser('ecget wind')
        assert parser.prog == 'ecget wind'

    @mock.patch('ecget.weather_amqp.DatamartConsumer')
    def test_take_action_makes_consumer(self, mock_DC, sh_wind):
        sh_wind.take_action(mock.Mock(lifetime=42))
        mock_DC.assert_called_once_with(
            queue_name='cmc.SoG.SandHeads',
            routing_key='exp.dd.notify.observations.swob-ml.*.CWVF',
            msg_handler=sh_wind._handle_msg,
            lifetime=42,
        )

    @mock.patch('ecget.weather_amqp.DatamartConsumer')
    def test_take_action_runs_consumer(self, mock_DC, sh_wind):
        sh_wind.take_action(mock.Mock(lifetime=42))
        mock_DC().run.assert_called_once_with()

    @mock.patch('ecget.SOG_weather.stevedore.driver.DriverManager')
    def test_handle_msg_log_msg_body_to_debug(self, mock_DM, sh_wind):
        sh_wind.log = mock.Mock()
        sh_wind._handle_msg('body')
        sh_wind.log.debug.assert_called_once_with('body')

    @mock.patch('ecget.SOG_weather.stevedore.driver.DriverManager')
    def test_handle_msg_driver_mgr(self, mock_DM, sh_wind):
        sh_wind._output_results = mock.Mock()
        sh_wind._handle_msg('body')
        mock_DM.assert_called_once_with(
            namespace='ecget.get_data',
            name='wind',
            invoke_on_load=True,
            invoke_args=('body',),
        )

    @mock.patch('ecget.SOG_weather.stevedore.driver.DriverManager')
    def test_handle_msg_get_data(self, mock_DM, sh_wind):
        sh_wind._output_results = mock.Mock()
        sh_wind._handle_msg('body')
        mock_DM().driver.get_data.assert_called_once_with(
            'avg_wnd_spd_10m_mt58-60', 'avg_wnd_dir_10m_mt58-60',
        )

    def test_calc_hourly_winds_timestamp(self, sh_wind):
        raw_data = {
            'timestamp': arrow.get(2014, 2, 7, 10),
            'avg_wnd_spd_10m_mt58-60': {'value': 0},
            'avg_wnd_dir_10m_mt58-60': {'value': 0},
        }
        hourly_winds = sh_wind._calc_hourly_winds(raw_data)
        timestamp = hourly_winds[0][0]
        assert timestamp == arrow.get(2014, 2, 7, 10).to('PST')

    def test_calc_hourly_winds_cross_wind(self, sh_wind):
        cross_strait_dir = math.degrees(sh_wind.STRAIT_HEADING) + 90
        raw_data = {
            'timestamp': arrow.get(2014, 2, 7, 10),
            'avg_wnd_spd_10m_mt58-60': {'value': 3.6},
            'avg_wnd_dir_10m_mt58-60': {'value': cross_strait_dir},
        }
        hourly_winds = sh_wind._calc_hourly_winds(raw_data)
        cross_wind = hourly_winds[0][1][0]
        expected = -1
        assert abs(cross_wind - expected) < 1e-4

    def test_calc_hourly_winds_along_wind(self, sh_wind):
        along_strait_dir = math.degrees(sh_wind.STRAIT_HEADING)
        raw_data = {
            'timestamp': arrow.get(2014, 2, 7, 10),
            'avg_wnd_spd_10m_mt58-60': {'value': 3.6},
            'avg_wnd_dir_10m_mt58-60': {'value': along_strait_dir},
        }
        hourly_winds = sh_wind._calc_hourly_winds(raw_data)
        along_wind = hourly_winds[0][1][1]
        expected = -1
        assert abs(along_wind - expected) < 1e-4
