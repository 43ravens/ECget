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


@pytest.mark.parametrize(
    'url', [
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-0000-CYVR-MAN-swob.xml'),
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-0900-CYVR-MAN-swob.xml'),
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-1400-CYVR-MAN-swob.xml'),
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-2000-CYVR-MAN-swob.xml'),
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-2300-CYVR-MAN-swob.xml'),
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-1400-CYVR-MAN-COR1-swob.xml'),
        ('http://-1800-swob.xml'),
    ]
)
def test_filter_match(url, dd_weather):
    dd_weather.url = url
    pattern = (
        r'.-'
        '([0-1]\d|'
        '2[0-3])'
        '00-.'
    )
    result = dd_weather.filter(pattern)
    assert result == url


@pytest.mark.parametrize(
    'url', [
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-0001-CYVR-MAN-swob.xml'),
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-2359-CYVR-MAN-swob.xml'),
        ('http://dd.weather.gc.ca/observations/swob-ml/20140220/CYVR/'
         '2014-02-20-1423-CYVR-MAN-COR1-swob.xml'),
        ('http://-1823-swob.xml'),
    ]
)
def test_filter_no_match(url, dd_weather):
    dd_weather.url = url
    pattern = (
        r'.-'
        '([0-1]\d|'
        '2[0-3])'
        '00-.'
    )
    result = dd_weather.filter(pattern)
    assert result is None


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_no_elements(mock_ET, mock_resp, dd_weather):
    mock_root_iter = mock.Mock(
        side_effect=[
            [[]],
            [[]],
        ])
    mock_root = mock.Mock(iter=mock_root_iter)
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data()
    assert data == {}


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_missing_id_elements(mock_ET, mock_resp, dd_weather):
    mock_root_iter = mock.Mock(
        side_effect=[
            IndexError,
            [[]],
        ])
    mock_root = mock.Mock(iter=mock_root_iter)
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data()
    assert data == {}


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_missing_data_elements(mock_ET, mock_resp, dd_weather):
    mock_root_iter = mock.Mock(
        side_effect=[
            [[]],
            IndexError,
        ])
    mock_root = mock.Mock(iter=mock_root_iter)
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data()
    assert data == {}


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_no_labels(mock_ET, mock_resp, dd_weather):
    id_elements = mock.Mock(
        attrib={'name': 'date_tm', 'value': '2014-02-06T18:00:00.000Z'}
    )
    data_elements = mock.Mock(
        attrib={'value': '100', 'name': 'rel_hum', 'uom': '%'}
    )
    mock_root_iter = mock.Mock(
        side_effect=[
            [[id_elements]],
            [[data_elements]],
        ])
    mock_root = mock.Mock(iter=mock_root_iter)
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data()
    assert data == {}


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_element_data_matches_label(mock_ET, mock_resp, dd_weather):
    id_elements = mock.Mock(
        attrib={'name': 'date_tm', 'value': '2014-02-06T18:00:00.000Z'}
    )
    data_elements = mock.Mock(
        attrib={'value': '100', 'name': 'rel_hum', 'uom': '%'}
    )
    mock_root_iter = mock.Mock(
        side_effect=[
            [[id_elements]],
            [[data_elements]],
        ])
    mock_root = mock.Mock(iter=mock_root_iter)
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data('rel_hum')
    assert data['rel_hum'] == {'value': '100', 'uom': '%'}


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_element_timestamp_matches_label(
    mock_ET, mock_resp, dd_weather,
):
    id_elements = mock.Mock(
        attrib={'name': 'date_tm', 'value': '2014-02-06T18:00:00.000Z'}
    )
    data_elements = mock.Mock(
        attrib={'value': '100', 'name': 'rel_hum', 'uom': '%'}
    )
    mock_root_iter = mock.Mock(
        side_effect=[
            [[id_elements]],
            [[data_elements]],
        ])
    mock_root = mock.Mock(iter=mock_root_iter)
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data('rel_hum')
    assert data['timestamp'] == '2014-02-06T18:00:00.000Z'


@mock.patch('ecget.weather_datamart.requests.get')
@mock.patch('ecget.weather_datamart.ET')
def test_get_data_element_data_matches_label_regex(
    mock_ET, mock_resp, dd_weather,
):
    id_elements = mock.Mock(
        attrib={'name': 'date_tm', 'value': '2014-02-06T18:00:00.000Z'}
    )
    data_elements = mock.Mock(
        attrib={'value': '100', 'name': 'rel_hum', 'uom': '%'}
    )
    mock_root_iter = mock.Mock(
        side_effect=[
            [[id_elements]],
            [[data_elements]],
        ])
    mock_root = mock.Mock(iter=mock_root_iter)
    mock_ET.fromstring.return_value = mock_root
    data = dd_weather.get_data(label_regexs=['rel_\w{3}'])
    assert data['rel_hum'] == {'value': '100', 'uom': '%'}
