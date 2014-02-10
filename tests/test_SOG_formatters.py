"""Unit tests for SOG_formatters module.

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
import arrow
import pytest


@pytest.fixture
def daily_value():
    import ecget.SOG_formatters
    return ecget.SOG_formatters.DailyValue()


@pytest.fixture
def hourly_wind():
    import ecget.SOG_formatters
    return ecget.SOG_formatters.HourlyWindComponents()


@pytest.fixture
def hourly_value():
    import ecget.SOG_formatters
    return ecget.SOG_formatters.HourlyValue()


@pytest.mark.parametrize(
    'data, expected',
    [
        ([(arrow.get(2014, 1, 22), 1234.567)],
         '2014 01 22 1.234567e+03\n'),
    ],
)
def test_DailyValue_format(data, expected, daily_value):
    line = next(daily_value.format(data))
    assert line == expected


@pytest.mark.parametrize(
    'data, expected',
    [
        ([(arrow.get(2014, 2, 9, 0, 0, 0), 5)],
         '2014 02 09 00 5.00\n'),
        ([(arrow.get(2014, 2, 9, 23, 0, 0), -2.142)],
         '2014 02 09 23 -2.14\n'),
    ],
)
def test_HourlyValue_format(data, expected, hourly_value):
    line = next(hourly_value.format(data))
    assert line == expected


@pytest.mark.parametrize(
    'data, expected',
    [
        ([(arrow.get(2014, 2, 6, 0, 0, 0), (-0.847842, 8.066742))],
         '06 02 2014 0.0 -0.8478 8.0667\n'),
        ([(arrow.get(2014, 2, 6, 23, 0, 0), (-0.8, 8.06))],
         '06 02 2014 23.0 -0.8000 8.0600\n'),
    ],
)
def test_HourlyWindComponents_format(data, expected, hourly_wind):
    line = next(hourly_wind.format(data))
    assert line == expected
