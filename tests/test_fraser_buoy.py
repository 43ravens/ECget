# Copyright 2014-2017 Doug Latornell and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for ECget fraser_buoy module.
"""
try:
    import unittest.mock as mock
except ImportError:  # pragma: no cover; happens for Python < 3.3
    import mock

import cliff.app
import pytest


@pytest.fixture
def fraser_water():
    import ecget.fraser_buoy
    return ecget.fraser_buoy.FraserWaterQuality(
        mock.Mock(spec=cliff.app.App), [])


def test_get_parser(fraser_water):
    parser = fraser_water.get_parser('ecget fraser water quality')
    assert parser.prog == 'ecget fraser water quality'
