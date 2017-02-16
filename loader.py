from pathlib import Path

from formats.UST import *

# TODO: 1 more sane format validation (multi-layered mb.)
# TODO: 2 enable extension correction for known modules

class Loader:
    module_formats = [UltimateSoundtracker, UltimateSoundtracker2,
                      SoundtrackerII, SoundtrackerIII, SoundtrackerIX,
                      MasterSoundtracker, SoundTracker2, NoiseTracker,
                      Protracker]

    class ModuleLoaderError(RuntimeError):
        pass

    @classmethod
    def load_file(cls, path: Path) -> dict:
        logging.debug("===========LOADING PATH: %s" % str(path))

        try:
            with open(path, 'rb') as mod_file:
                data = mod_file.read()
        except (IOError, OSError):
            s = "%s cannot be read" % str(path)
            logging.error(s)
            raise cls.ModuleLoaderError(s)

        extension_compatible = cls.module_formats.copy()
        for module_format in cls.module_formats:
            if not module_format.validate_extension(path.name, path.suffix):
                extension_compatible.remove(module_format)

        flag_bytes_compatible = cls.module_formats.copy()
        for module_format in cls.module_formats:
            if not module_format.validate(data, validation_level=0):
                flag_bytes_compatible.remove(module_format)

        zero_bytes_compatible = cls.module_formats.copy()
        for module_format in cls.module_formats:
            if not module_format.validate(data, validation_level=1):
                zero_bytes_compatible.remove(module_format)

        guess_bytes_compatible = cls.module_formats.copy()
        for module_format in cls.module_formats:
            if not module_format.validate(data, validation_level=2):
                guess_bytes_compatible.remove(module_format)

        for module_format in zero_bytes_compatible:
            try:
                logging.debug('Trying to load as %s' % module_format.name)
                module = module_format.load(data)
            except module_format.ModuleFormatError:
                continue
            else:
                module['format'] = module_format
                module['filename'] = path.name
                return module
