"""ECget application.

Get Environment Canada weather & hydrometric data.

This module is connected to the `ecget` command via a console_scripts
entry point in setup.py.

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
import sys

import cliff.app
import cliff.commandmanager

import __pkg_metadata__


class ECgetApp(cliff.app.App):
    def __init__(self):
        super(ECgetApp, self).__init__(
            description=__pkg_metadata__.DESCRIPTION,
            version=__pkg_metadata__.VERSION,
            command_manager=cliff.commandmanager.CommandManager('ecget.app'),
        )


def main(argv=sys.argv[1:]):
    app = ECgetApp()
    return app.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
