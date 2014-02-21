# Copyright 2014 Doug Latornell and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for ECget river module.
"""
try:
    import unittest.mock as mock
except ImportError:     # pragma: no cover; happens for Python < 3.3
    import mock

import arrow
import bs4
import cliff.app
import pytest
import stevedore.driver


@pytest.fixture
def river_flow():
    import ecget.river
    return ecget.river.RiverFlow(mock.Mock(spec=cliff.app.App), [])


@pytest.fixture
def daily_value_mgr():
    import ecget.SOG_formatters
    driver = mock.Mock(
        name='daily_value',
        obj=ecget.SOG_formatters.DailyValue(),
    )
    return stevedore.driver.DriverManager.make_test_instance(driver)


def test_get_parser(river_flow):
    parser = river_flow.get_parser('ecget river flow')
    assert parser.prog == 'ecget river flow'


def test_take_action_end_date_None(river_flow):
    start_date = arrow.get(2014, 1, 22)
    parsed_args = mock.Mock(
        station_id='foo',
        start_date=start_date,
        end_date=None,
    )
    river_flow._get_data = mock.Mock()
    river_flow._calc_daily_avgs = mock.Mock(return_value=[])
    river_flow._output_results = mock.Mock()
    river_flow.take_action(parsed_args)
    assert parsed_args.end_date == start_date


def test_take_action_interpolate_missing_if_necessary(river_flow):
    parsed_args = mock.Mock(
        station_id='foo',
        start_date=arrow.get(2014, 1, 22),
        end_date=arrow.get(2014, 1, 23),
    )
    river_flow._get_data = mock.Mock()
    mock_avgs = range(2)
    river_flow._calc_daily_avgs = mock.Mock(return_value=mock_avgs)
    river_flow._interpolate_missing = mock.Mock()
    river_flow._output_results = mock.Mock()
    river_flow.take_action(parsed_args)
    river_flow._interpolate_missing.assert_called_once_with(mock_avgs)


def test_calc_daily_avgs_1_row(river_flow):
    html = '''
        <table>
          <tr>
            <td>2014-01-21 19:02:00</td>
            <td>4200.0</td>
          </tr>
        </table>
    '''
    raw_data = bs4.BeautifulSoup(html)
    daily_avgs = river_flow._calc_daily_avgs(raw_data, arrow.get(2014, 1, 22))
    assert daily_avgs == [(arrow.get(2014, 1, 21), 4200.0)]


def test_calc_daily_avgs_2_rows_1_day(river_flow):
    html = '''
        <table>
          <tr>
            <td>2014-01-21 19:02:00</td>
            <td>4200.0</td>
          </tr>
          <tr>
            <td>2014-01-21 19:07:00</td>
            <td>4400.0</td>
          </tr>
        </table>
    '''
    raw_data = bs4.BeautifulSoup(html)
    daily_avgs = river_flow._calc_daily_avgs(raw_data, arrow.get(2014, 1, 22))
    assert daily_avgs == [(arrow.get(2014, 1, 21), 4300.0)]


def test_calc_daily_avgs_2_rows_2_days(river_flow):
    html = '''
        <table>
          <tr>
            <td>2014-01-21 19:02:00</td>
            <td>4200.0</td>
          </tr>
          <tr>
            <td>2014-01-22 19:07:00</td>
            <td>4400.0</td>
          </tr>
        </table>
    '''
    raw_data = bs4.BeautifulSoup(html)
    daily_avgs = river_flow._calc_daily_avgs(raw_data, arrow.get(2014, 1, 23))
    expected = [
        (arrow.get(2014, 1, 21), 4200.0),
        (arrow.get(2014, 1, 22), 4400.0),
    ]
    assert daily_avgs == expected


def test_calc_daily_avgs_end_date(river_flow):
    html = '''
        <table>
          <tr>
            <td>2014-01-21 19:02:00</td>
            <td>4200.0</td>
          </tr>
          <tr>
            <td>2014-01-22 19:07:00</td>
            <td>4400.0</td>
          </tr>
        </table>
    '''
    raw_data = bs4.BeautifulSoup(html)
    daily_avgs = river_flow._calc_daily_avgs(raw_data, arrow.get(2014, 1, 21))
    assert daily_avgs == [(arrow.get(2014, 1, 21), 4200.0)]


def test_read_datestamp(river_flow):
    datestamp = river_flow._read_datestamp('2014-01-22 18:16:42')
    assert datestamp == arrow.get(2014, 1, 22)


@pytest.mark.parametrize(
    'input, expected', [
        ('4200.0', 4200.0),
        ('4200.0*', 4200.0),
    ]
)
def test_convert_flow(river_flow, input, expected):
    flow = river_flow._convert_flow(input)
    assert flow == expected


def test_interpolate_missing_no_gap(river_flow):
    daily_avgs = [
        (arrow.get(2014, 1, 22), 4300.0),
        (arrow.get(2014, 1, 23), 4500.0),
    ]
    river_flow.log = mock.Mock()
    river_flow._interpolate_values = mock.Mock()
    river_flow._interpolate_missing(daily_avgs)
    assert len(daily_avgs) == 2
    assert not river_flow.log.debug.called
    assert not river_flow._interpolate_values.called


def test_interpolate_missing_1_day_gap(river_flow):
    daily_avgs = [
        (arrow.get(2014, 1, 22), 4300.0),
        (arrow.get(2014, 1, 24), 4500.0),
    ]
    river_flow.log = mock.Mock()
    river_flow._interpolate_values = mock.Mock()
    river_flow._interpolate_missing(daily_avgs)
    expected = (arrow.get(2014, 1, 23), None)
    assert daily_avgs[1] == expected
    river_flow.log.debug.assert_called_once_with(
        'interpolated average flow for 2014-01-23')
    river_flow._interpolate_values.assert_called_once_with(daily_avgs, 1, 1)


def test_interpolate_missing_2_day_gap(river_flow):
    daily_avgs = [
        (arrow.get(2014, 1, 22), 4300.0),
        (arrow.get(2014, 1, 25), 4600.0),
    ]
    river_flow.log = mock.Mock()
    river_flow._interpolate_values = mock.Mock()
    river_flow._interpolate_missing(daily_avgs)
    expected = [
        (arrow.get(2014, 1, 23), None),
        (arrow.get(2014, 1, 24), None),
    ]
    assert daily_avgs[1:3] == expected
    expected = [
        mock.call('interpolated average flow for 2014-01-23'),
        mock.call('interpolated average flow for 2014-01-24'),
    ]
    river_flow.log.debug.call_args_list == expected
    river_flow._interpolate_values.assert_called_once_with(daily_avgs, 1, 2)


def test_interpolate_missing_2_gaps(river_flow):
    daily_avgs = [
        (arrow.get(2014, 1, 22), 4300.0),
        (arrow.get(2014, 1, 24), 4500.0),
        (arrow.get(2014, 1, 25), 4500.0),
        (arrow.get(2014, 1, 28), 4200.0),
    ]
    river_flow.log = mock.Mock()
    river_flow._interpolate_values = mock.Mock()
    river_flow._interpolate_missing(daily_avgs)
    expected = (arrow.get(2014, 1, 23), None)
    assert daily_avgs[1] == expected
    expected = [
        (arrow.get(2014, 1, 26), None),
        (arrow.get(2014, 1, 27), None),
    ]
    assert daily_avgs[4:6] == expected
    expected = [
        mock.call('interpolated average flow for 2014-01-23'),
        mock.call('interpolated average flow for 2014-01-26'),
        mock.call('interpolated average flow for 2014-01-27'),
    ]
    river_flow.log.debug.call_args_list == expected
    expected = [
        mock.call(daily_avgs, 1, 1),
        mock.call(daily_avgs, 4, 5),
    ]
    assert river_flow._interpolate_values.call_args_list == expected


def test_interpolate_values_1_day_gap(river_flow):
    daily_avgs = [
        (arrow.get(2014, 1, 22), 4300.0),
        (arrow.get(2014, 1, 23), None),
        (arrow.get(2014, 1, 24), 4500.0),
    ]
    river_flow._interpolate_values(daily_avgs, 1, 1)
    assert daily_avgs[1] == (arrow.get(2014, 1, 23), 4400.0)


def test_interpolate_values_2_day_gap(river_flow):
    daily_avgs = [
        (arrow.get(2014, 1, 22), 4300.0),
        (arrow.get(2014, 1, 23), None),
        (arrow.get(2014, 1, 24), None),
        (arrow.get(2014, 1, 25), 4600.0),
    ]
    river_flow._interpolate_values(daily_avgs, 1, 2)
    expected = [
        (arrow.get(2014, 1, 23), 4400.0),
        (arrow.get(2014, 1, 24), 4500.0),
    ]
    assert daily_avgs[1:3] == expected


def test_output_results(daily_value_mgr, river_flow, capsys):
    river_flow._output_results([(arrow.get(2014, 1, 23), 4200.0)])
    out, err = capsys.readouterr()
    assert out == '2014 01 23 4.200000e+03\n'
