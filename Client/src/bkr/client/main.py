#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import sys
from optparse import Option, IndentedHelpFormatter

from kobo.cli import CommandOptionParser
from bkr.client import CONF


try:

    # kobo 0.3+
    import kobo.conf
    from kobo.client import ClientCommandContainer

    class BeakerCommandContainer(ClientCommandContainer):
        def __init__(self, conf_file=None, **kwargs):
            conf = kobo.conf.PyConfigParser()
            conf.load_from_file(conf_file)
            ClientCommandContainer.__init__(self, conf=conf, **kwargs)

    CommandContainerClass = BeakerCommandContainer

except:

    # kobo 0.2
    from kobo.cli import CommandContainer

    # can not use subclass due to bug in kobo-0.2: super(cls, cls) is causing
    # infinite recursion when register_module is used with subclass:
    def BeakerCommandContainer(conf_file=None, **kwargs):
        os.environ[CONF] = conf_file
        return CommandContainer(**kwargs)

    CommandContainerClass = CommandContainer


__all__ = (
    "main",
)


# register default command plugins
import bkr.client.commands
CommandContainerClass.register_module(bkr.client.commands, prefix="cmd_")


def main():
    conf_file = os.getenv(CONF, '')
    if not conf_file:
        user_conf = os.path.expanduser('~/.beaker_client/config')
        old_conf = os.path.expanduser('~/.beaker')
        if os.path.exists(user_conf):
            conf_file = user_conf
        elif os.path.exists(old_conf):
            sys.stderr.write(
                    "%s is deprecated for config, please use %s instead\n" %
                    (old_conf, user_conf))
            conf_file = old_conf
        else:
            conf_file = "/etc/beaker/client.conf"
            sys.stderr.write("%s not found, using %s\n" %
                    (user_conf, conf_file))
    command_container = BeakerCommandContainer(conf_file=conf_file)

    option_list = [
        Option("--username", help="specify user"),
        Option("--password", help="specify password"),
    ]

    formatter = IndentedHelpFormatter(max_help_position=60, width=120)
    parser = CommandOptionParser(command_container=command_container, default_command="help", formatter=formatter)
    parser._populate_option_list(option_list, add_help=False)
    return parser.run()

if __name__ == '__main__':
    main()
