import argparse
import asyncio
import json
import os
import __main__
from typing import Callable, Coroutine, Optional

from core.utilities import get_or_none

default_args_fname = '.default_args.json'

class Bootstrapper:
    def __init__(self, script_description):
        self.__arg_parser = argparse.ArgumentParser(
            prog=os.path.basename(__main__.__file__),
            description=script_description)
        
        try:
            with open(default_args_fname, 'r', encoding='utf8') as f:
                self.__default_args = json.load(f)
        except FileNotFoundError:
            self.__default_args = {}

        self.add_argument('-ip', '--bambu-ip', help="IP of your bambu printer. Eg. 192.168.1.100")
        self.add_argument('-sn', '--bambu-sn', help="SN of your bambu printer. Required to subscribe to MQTT channel.")
        self.add_argument('-ac', '--bambu-ac', help="Access code of your bambu printer")

    def add_argument(self, short: str, explicit: str, help: str):
        default = get_or_none(self.__default_args, explicit.strip('-').replace('-', '_'))
        self.__arg_parser.add_argument(short, explicit, default=default, required=default is None, help=help)

    def run(self, main: Callable[[argparse.Namespace], Coroutine]):
        args = self.__arg_parser.parse_args()
        args_dict = vars(args)

        for k in args_dict:
            self.__default_args[k] = args_dict[k]

        with open(default_args_fname, 'w', encoding='utf8') as f:
            json.dump(self.__default_args, f, indent=2)

        asyncio.run(main(args))
