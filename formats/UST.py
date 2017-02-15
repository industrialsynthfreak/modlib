import struct
import string
import logging

from .module_format import ModuleFormat
from . import ModuleFormatMeta


class UltimateSoundtracker(ModuleFormat, metaclass=ModuleFormatMeta):
    name = "Ultimate Soundtracker 1.2"
    description = "an original 1987 tracker for AMIGA"
    author = 'Karsten Obarski'
    extensions = ("MOD", "UST")
    encoding = 'ascii'

    tracks = 4
    samples = 15
    positions = 128
    rows = 64
    patterns = 128
    effects = {'ARP': 0x100, 'PORTA': 0x200, 'NONE': 0x000}

    sample_rate = 16574
    sample_width = 2
    channels = 1

    _name_not_recommended = string.ascii_lowercase
    _name_size = 20
    _sample_name_size = 22
    _sample_header_size = 30
    _sample_header = '>%dsHHHH' % _sample_name_size
    _sample_max_volume = 0x40
    _sample_max_size = 9999
    _sample_recommended_size = 9900

    _song_header = '>BB%dB' % positions

    _pattern_value_size = 4
    _pattern_value_header = '>%di' % (rows * tracks)
    _pattern_size = tracks * rows * _pattern_value_size

    _flag_bytes = dict()
    _zeros = dict()
    _guess_bytes = {471: b'\x78'}

    @classmethod
    def load(cls, data: bytes) -> dict:
        """Load module data from a file."""
        logging.debug('=====Loading an %s module=====' % cls.name)
        module = dict()
        try:
            offset, end = 0, cls._name_size
            module['name'] = cls.decode_string(data[offset:end])

            module['samples'] = dict()
            for i in range(cls.samples):
                logging.debug('---Loading sample #%d:---' % i)
                offset = end
                end = offset + cls._sample_header_size
                logging.debug('Offset %d:%d' % (offset, end))
                module['samples'][i] = cls._load_sample_headers(
                    data[offset:end])

            logging.debug('---Loading song data---')
            offset = end
            end = offset + 2 + cls.positions
            logging.debug('Offset %d:%d' % (offset, end))
            module.update(cls._load_song_header(data[offset:end]))

            module['patterns'] = dict()
            for i in range(module['max_pattern_number'] + 1):
                logging.debug('---Loading pattern $%d:---' % i)
                offset = end
                end = offset + cls._pattern_size
                logging.debug('Offset %d:%d' % (offset, end))
                module['patterns'][i] = cls._load_pattern(data[offset:end])

            for i, sample in module['samples'].items():
                if not sample or not sample['length']:
                    continue
                logging.debug('---Loading raw data for sample #%d' % i)
                offset = end
                end = offset + sample['length']
                logging.debug('Offset %d:%d' % (offset, end))
                sample['data'] = cls._load_raw(data[offset:end])

            if len(data) > end:
                s = "Some data left at the end of the file. This can't be " \
                    "good. %s unused bytes found" % (len(data) - end)
                logging.warning(s)

        except IndexError:
            s = "POSSIBLY corrupt data: end of file reached while scanning"
            if module['patterns']:
                logging.warning(s)
            else:
                logging.error(s)
                raise cls.ModuleFormatError(s)
        logging.debug('===========SUCCESS===========')
        return module

    @classmethod
    def _load_sample_headers(cls, data: bytes) -> dict:

        def validate():
            if volume > cls._sample_max_volume:
                s = "Unexpected volume value: %d, expected <= %d" % (
                    volume, cls._sample_max_volume)
                logging.error(s)
                raise cls.ModuleFormatError(s)
            elif length > cls._sample_max_size:
                s = "Sample length too big: %d, expected <= %d" % (
                    length, cls._sample_max_size)
                logging.error(s)
                raise cls.ModuleFormatError(s)
            elif repeat_offset > length:
                s = "Sample repeat offset is greater than the sample length:" \
                    " %d > %d" % (repeat_offset, length)
                logging.error(s)
                raise cls.ModuleFormatError(s)
            elif loop and repeat_length > (
                        length - repeat_offset):
                s = "Sample repeat length is greater than the possible loop " \
                    "length: %d, with length: %d, offset: %d" % (
                    repeat_length, length, repeat_offset)
                logging.error(s)
                raise cls.ModuleFormatError(s)
            if length > cls._sample_recommended_size:
                s = "Sample length is greater than recommended: %d, " \
                    "expected <= %d" % (length, cls._sample_recommended_size)
                logging.warning(s)
            if repeat_length == 0:
                s = "'No repeat' flag should be marked with 1, not 0."
                logging.warning(s)
            if repeat_offset % 2:
                s = "Repeat offset is an odd number."
                logging.warning(s)

        name, length, volume, repeat_offset, repeat_length = struct.unpack(
            cls._sample_header, data)
        name = cls.decode_string(name)

        if all((i == 0 for i in (len(name), length, volume, repeat_offset,
                                 repeat_length))):
            return None

        length *= 2
        if repeat_length < 2:
            loop = False
        else:
            loop = True
            repeat_length *= 2

        validate()

        sample = {
            'name': name,
            'length': length,
            'volume': volume,
            'repeat_offset': repeat_offset,
            'loop': loop,
            'repeat_length': repeat_length,
            'data': None
        }

        return sample

    @classmethod
    def _load_song_header(cls, data: bytes) -> dict:

        def validate():
            if length > cls.positions:
                s = "Song length is bigger than allowed number of positions:" \
                    " %d while expected <= %d" % (length, cls.positions)
                logging.error(s)
                raise cls.ModuleFormatError(s)
            if tempo == 0:
                s = "Song tempo is 0."
                logging.warning(s)
            for p in positions[length:]:
                if p != 0:
                    s = "Non-empty positions found beyond the declared length."
                    logging.warning(s)
                    break

        values = struct.unpack(cls._song_header, data)
        length, tempo, positions = values[0], values[1], values[2:]
        mp = max(positions)

        validate()

        song = {
            'length': length,
            'tempo': tempo,
            'positions': positions,
            'max_pattern_number': mp
        }

        return song

    @classmethod
    def _load_pattern(cls, data: bytes) -> list:

        def validate():
            if (effect & 0xf00) not in cls.effects.values():
                s = "Unknown effect value %d" % effect
                logging.warning(s)

        rows = struct.unpack(cls._pattern_value_header, data)
        pattern = [[] for _ in range(cls.tracks)]
        for i, row in enumerate(rows):
            effect = row & 0xfff
            tone = (row >> 16) & 0xfff
            sample = ((row >> 24) & 0xf0) + ((row >> 12) & 0xf)

            validate()

            pattern[i % cls.tracks].append([sample, tone, effect])

        return pattern

    @classmethod
    def _load_raw(cls, data: bytes) -> bytes:
        if data[0] != 0:
            s = 'No zero pad at the start of the raw sample data.'
            logging.warning(s)
        if data[-1] != 0:
            s = 'No zero pad at the end of the raw sample data.'
            logging.warning(s)
        return data

    @classmethod
    def _generate_zero_pads(cls):
        """Called once in a metaclass to construct zero pads."""
        offset = cls._name_size - 1
        cls._zeros[offset] = b'\x00'
        offset += cls._sample_name_size
        for i in range(cls.samples):
            cls._zeros[offset] = b'\x00'
            cls._zeros[offset + 3] = b'\x00'
            offset += cls._sample_header_size
