#!/usr/bin/python3

import glob
import logging
import sys
import os

from loader import Loader
from unpacker import Unpacker


class Console:
    FORMAT = '%(message)s'
    VERBOSE = 'v'
    LOG = 'modlib.log'
    IGNORED_PREFIXES = {'.', '$', '~', '__'}

    def __init__(self, args: tuple):
        self.flags = set()
        paths = self.parse_args(args)
        if self.VERBOSE in self.flags:
            logging.basicConfig(level=logging.DEBUG, format=self.FORMAT,
                                stream=sys.stdout)
        else:
            logging.basicConfig(filemode='w', level=logging.DEBUG,
                                format=self.FORMAT, filename=self.LOG)
        for filepath in paths:
            if os.path.isfile(filepath):
                path, filename, name, ext = self.parse_file_path(filepath)
                if self.validate_file_name(filename):
                    self.load_path(filepath, filename, ext)

    def parse_file_path(self, path: str) -> tuple:
        path, filename = os.path.split(path)
        split = path.split('.')
        if len(split) < 2:
            name = split[0]
            ext = ""
        else:
            name = "".join(split[:-1])
            ext = split[-1]
        return path, filename, name, ext

    def validate_file_name(self, filename: str) -> bool:
        for pref in self.IGNORED_PREFIXES:
            if filename.startswith(pref):
                logging.debug("Ignoring system/hidden file %s" % filename)
                return False
        else:
            return True

    def load_path(self, filepath: str, filename: str, ext: str):
        try:
            module = Loader.load_file(filepath, filename, ext)
        except Loader.ModuleLoaderError:
            msg = "Cannot load path: %s" % filepath
            logging.error(msg)
            return None
        else:
            return module

    def unpack_data(self, data: dict):
        try:
            Unpacker.unpack(data)
        except Unpacker.ModuleUnpackerError:
            msg = "Cannot unpack path: %s" % path
            logging.error(msg)

    def parse_args(self, args: tuple):
        paths = []
        for arg in args:
            if arg.startswith('--'):
                self.flags.add(arg[2:].upper())
            elif arg.startswith('-'):
                for letter in arg[1:]:
                    self.flags.add(letter)
            else:
                paths.extend(glob.glob(arg))
        return paths


if __name__ == "__main__":
    console = Console(sys.argv[1:])
    exit(0)
