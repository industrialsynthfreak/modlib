#!/usr/bin/env python3

import logging
import sys

from pathlib import Path

from loader import Loader
from unpacker import Unpacker


class Console:
    FORMAT = '%(message)s'
    VERBOSE = 'v'
    LOG = 'modlib.log'
    WORKING_DIR = Path('.')
    PROJECT_SUFFIX = '_unpacked'

    def __init__(self, args: tuple):
        self.flags = set()
        paths = self._parse_args(args)
        self._set_up_logger()
        modules = self.load_paths(paths)
        self.unpack_data(modules)

    @staticmethod
    def load_paths(paths: list) -> list:
        logging.debug('LOADING:')

        loaded_modules = []
        for path in paths:
            if path.is_file():
                try:
                    # TODO: Actually it shouldn't return NoneType
                    # Must always rise an exception
                    module = Loader.load_file(path)
                    if module:
                        loaded_modules.append(module)
                except Loader.ModuleLoaderError:
                    msg = "Cannot load path: %s" % str(path)
                    logging.error(msg)

        return loaded_modules

    def unpack_data(self, modules: list):
        logging.debug('UNPACKING:')

        for module in modules:
            project_path = self.WORKING_DIR / ("%s%s" % (module['filename'],
                                                         self.PROJECT_SUFFIX))
            sample_path = project_path / 'samples'
            try:
                project_path.mkdir(exist_ok=True)
                sample_path.mkdir(exist_ok=True)
            except (IOError, OSError):
                msg = "Cannot create folders %s, %s at the working dir %s" % (
                    project_path.resolve(), sample_path.resolve(),
                    self.WORKING_DIR.resolve()
                )
                logging.error(msg)
                return
            try:
                Unpacker.unpack(module, project_path, sample_path)
            except Unpacker.ModuleUnpackerError:
                msg = "Cannot unpack module: %s" % module.name
                logging.error(msg)

    def _parse_args(self, args: tuple) -> list:
        paths = []
        for arg in args:
            if arg.startswith('--'):
                self.flags.add(arg[2:].upper())
            elif arg.startswith('-'):
                for letter in arg[1:]:
                    self.flags.add(letter)
            else:
                paths.extend(list(self.WORKING_DIR.glob(arg)))
        return paths

    def _set_up_logger(self):
        if self.VERBOSE in self.flags:
            logging.basicConfig(level=logging.DEBUG, format=self.FORMAT,
                                stream=sys.stdout)
        else:
            logging.basicConfig(filemode='w', level=logging.DEBUG,
                                format=self.FORMAT, filename=self.LOG)


if __name__ == "__main__":
    console = Console(sys.argv[1:])
    exit(0)
