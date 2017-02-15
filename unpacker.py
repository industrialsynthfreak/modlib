import logging
import json
import wave
import string
import os


# TODO: Settings for .zip/.xz archive creation instead of a folder

class Unpacker:
    audio_prefix = ""
    safe_characters = string.ascii_letters + string.digits + "~ -_."
    sample_dir = "samples"

    class ModuleUnpackerError(RuntimeError):
        pass

    @classmethod
    def make_a_filename(cls, name: str) -> str:
        return ''.join([s for s in name if s in cls.safe_characters])

    @classmethod
    def encode_wav(cls, filepath: str, data: bytes, sample_width: int,
                   sample_rate: int, channels: int):
        wav = wave.open(filepath, 'wb')
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(data)
        wav.close()

    @classmethod
    def unpack(cls, data: dict, filename=None):
        logging.debug('Unpacking module data.')

        if not filename:
            filename = data['name']

        module_format = data['format']

        filename = cls.make_a_filename(filename)
        dirname = "%s_unpacked" % filename
        sample_dir = "%s/%s" % (dirname, cls.sample_dir)

        try:
            if not os.path.exists(dirname):
                os.makedirs(dirname)
                os.makedirs(sample_dir)
            else:
                if not os.path.exists(sample_dir):
                    os.makedirs(sample_dir)

            for i, sample in data['samples'].items():
                if not sample or not sample['data']:
                    continue
                else:
                    name = cls.make_a_filename(sample['name'])
                    audio_name = "%s/%02d %s%s.wav" % (cls.sample_dir, i + 1,
                                                     cls.audio_prefix, name)
                    audio_path = "%s/%s" % (dirname, audio_name)
                    cls.encode_wav(audio_path, data=sample['data'],
                                   sample_width=module_format.sample_width,
                                   sample_rate=module_format.sample_rate,
                                   channels=module_format.channels)
                    sample['data'] = audio_name

            data['format'] = module_format.name
            path = "%s/%s.json" % (dirname, filename)
            with open(path, 'w') as dumpfile:
                dumpfile.write(json.dumps(data, skipkeys=True))
        except (OSError, IOError):
            s = "Cannot create/write files. Maybe a permissions problem. " \
                "Aborting..."
            logging.error(s)
            raise cls.ModuleUnpackerError(s)
        else:
            logging.debug("===========SUCCESS===========")
