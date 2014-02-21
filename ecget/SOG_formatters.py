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

"""Drivers to format data for SOG forcing files.
"""
import abc


__all__ = [
    'FormatterBase', 'DailyValue', 'HourlyValue', 'HourlyWindComponents',
]


class FormatterBase(object):
    """Base class for SOG forcing file data formatters.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def format(self, data):
        """Format the data and return a line of text.

        :arg data: An iterable of 2-tuples containing dates or datetimes
                   and data values.

        :returns: Iterable producing the formatted text.
        """


class DailyValue(FormatterBase):
    """Format date-stamped values as YYYY MM DD VALUE
    with VALUE in scientific notation.
    """
    def format(self, data):
        """Format the data and return a line of text.

        :arg data: An iterable of 2-tuples containing dates and data values.

        :returns: Iterable producing the formatted text.
        """
        for date, value in data:
            line = '{date} {value:e}\n'.format(
                date=date.format('YYYY MM DD'),
                value=value,
            )
            yield line


class HourlyValue(FormatterBase):
    """Format date-stamped values as YYYY MM DD HH VALUE
    with VALUE to 2 decimal place precision.
    """
    def format(self, data):
        """Format the data and return a line of text.

        :arg data: An iterable of 2-tuples containing timestamps
                   and data values.

        :returns: Iterable producing the formatted text.
        """
        for timestamp, value in data:
            line = '{timestamp} {value:.2f}\n'.format(
                timestamp=timestamp.format('YYYY MM DD HH'),
                value=value,
            )
            yield line


class HourlyWindComponents(FormatterBase):
    """Format time-stamped hourly wind components
    as DD MM YYYY HH.0 CROSS ALONG,
    where CROSS and ALONG are the wind components with 4 decimal place
    precision.
    """
    def format(self, data):
        """Format the data and return a line of text.

        :arg data: An iterable of 2-tuples containing timestamps
                   and a (cross-strait, along-strait) wind component
                   tuple.

        :returns: Iterable producing the formatted text.
        """
        for timestamp, components in data:
            line = (
                '{date} {hour:.1f} {cross_wind:.4f} {along_wind:.4f}\n'
                .format(
                    date=timestamp.format('DD MM YYYY'),
                    hour=timestamp.hour,
                    cross_wind=components[0],
                    along_wind=components[1],
                )
            )
            yield line
