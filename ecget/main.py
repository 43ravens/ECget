"""ECget application

The ecget command runs this module.
"""
import sys
from cliff.app import App
from cliff.commandmanager import CommandManager


class ECgetApp(App):
    def __init__(self):
        super(ECgetApp, self).__init__(
            # TODO: Need a DRY way to get description and version here
            #       and in setup.py
            description='Get Environment Canada Weather & Hydrometric Data',
            version='0.1',
            command_manager=CommandManager('ecget.app'),
        )


def main(argv=sys.argv[1:]):
    app = ECgetApp()
    return app.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
