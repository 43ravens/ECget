"""Unit tests for ECget weather_datamart module.

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

import pytest


@pytest.fixture
def dd_weather():
    import ecget.weather_datamart
    return ecget.weather_datamart.DatamartWeather('url')


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_no_elements(mock_ET, mock_resp, dd_weather):
    mock_root = mock.Mock(iter=mock.Mock(return_value=[]))
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data()
    assert data == {}


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_no_labels(mock_ET, mock_resp, dd_weather):
    mock_el = mock.Mock(
        attrib={'value': '100', 'name': 'rel_hum', 'uom': '%'}
    )
    mock_root = mock.Mock(iter=mock.Mock(return_value=[[mock_el]]))
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data()
    assert data == {}


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_element_matches_label(mock_ET, mock_resp, dd_weather):
    mock_el = mock.Mock(
        attrib={'value': '100', 'name': 'rel_hum', 'uom': '%'}
    )
    mock_root = mock.Mock(iter=mock.Mock(return_value=[[mock_el]]))
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data('rel_hum')
    assert data == {'rel_hum': {'value': '100', 'uom': '%'}}
