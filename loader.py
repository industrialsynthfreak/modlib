import logging
import os

import formats, formats.UST


class Loader:
    module_formats = formats.ModuleFormatMeta.formats

    class ModuleLoaderError(RuntimeError):
        pass

    @classmethod
    def load_file(cls, filepath: str, filename: str, ext: str) -> dict:
        logging.debug("===========LOADING PATH: %s" % filepath)

        try:
            with open(filepath, 'rb') as mod_file:
                data = mod_file.read()
        except (IOError, OSError):
            s = "%s cannot be read" % filepath
            logging.error(s)
            raise cls.ModuleLoaderError(s)

        extension_compatible = cls.module_formats.copy()
        for format in cls.module_formats:
            if not format.validate_extension(filename, ext):
                extension_compatible.remove(format)

        flag_bytes_compatible = cls.module_formats.copy()
        for format in cls.module_formats:
            if not format.validate(data, validation_level=0):
                flag_bytes_compatible.remove(format)

        zero_bytes_compatible = cls.module_formats.copy()
        for format in cls.module_formats:
            if not format.validate(data, validation_level=1):
                zero_bytes_compatible.remove(format)

        guess_bytes_compatible = cls.module_formats.copy()
        for format in cls.module_formats:
            if not format.validate(data, validation_level=2):
                guess_bytes_compatible.remove(format)

        for format in zero_bytes_compatible:
            try:
                module = format.load(data)
            except format.ModuleFormatError:
                continue
            else:
                module['format'] = format
                return module
