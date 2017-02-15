import logging
import json
import wave
import string

from pathlib import Path


# TODO: Settings for .zip/.xz archive creation instead of a folder

class Unpacker:
    safe_characters = string.ascii_letters + string.digits + "~ -_."

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
    def unpack(cls, data: dict, project_path: Path, sample_path: Path):
        logging.debug('Unpacking module data.')

        module_format = data['format']

        try:
            for i, sample in data['samples'].items():
                if not sample or not sample['data']:
                    continue
                else:
                    name = cls.make_a_filename(sample['name'])
                    audio_name = "%02d %s.wav" % (i + 1, name)
                    audio_path = sample_path / audio_name
                    cls.encode_wav(str(audio_path), data=sample['data'],
                                   sample_width=module_format.sample_width,
                                   sample_rate=module_format.sample_rate,
                                   channels=module_format.channels)
                    sample['data'] = sample_path.suffix + audio_name

            data['format'] = module_format.name
            module_path = project_path / ("%s.json" % data['filename'])
            with open(module_path, 'w') as dumpfile:
                dumpfile.write(json.dumps(data, skipkeys=True))

        except (OSError, IOError):
            s = "Cannot create/write files. Maybe a permissions problem. " \
                "Aborting..."
            logging.error(s)
            raise cls.ModuleUnpackerError(s)
        else:
            logging.debug("===========SUCCESS===========")
