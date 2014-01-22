"""Drivers to format data for SOG forcing files.

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
import abc


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
            line = '{date:%Y %m %d} {value:e}\n'.format(
                date=date,
                value=value,
            )
            yield line
