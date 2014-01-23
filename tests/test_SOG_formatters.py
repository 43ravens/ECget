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
import datetime

import pytest


@pytest.fixture
def daily_value():
    import ecget.SOG_formatters
    return ecget.SOG_formatters.DailyValue()


def test_DailyValue_format(daily_value):
    data = [(datetime.date(2014, 1, 22), 1234.567)]
    line = next(daily_value.format(data))
    assert line == '2014 01 22 1.234567e+03\n'
