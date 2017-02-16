import struct
import string
import logging

from typing import Optional

from .module_format import ModuleFormat
from . import ModuleFormatMeta


class UltimateSoundtracker(ModuleFormat, metaclass=ModuleFormatMeta):
    name = "Ultimate Soundtracker 1"
    description = "an original 1987 Ultimate Soundtracker 1.0-1.21"
    author = 'Karsten Obarski'
    extensions = ("MOD", "UST", "UST10", "UST11", "UST12")
    encoding = 'ascii'

    tracks = 4
    samples = 15
    positions = 128
    rows = 64
    patterns = 64
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
    _sample_max_size = 9998
    _sample_recommended_size = 9900
    _sample_prefix = None

    _song_header = '>BB%dB' % positions

    _pattern_value_size = 4
    _pattern_value_header = '>%di' % (rows * tracks)
    _pattern_size = tracks * rows * _pattern_value_size

    _flag_bytes = {471: b'\x78'}
    _zeros = {}
    _guess_bytes = {}

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
    def _load_sample_headers(cls, data: bytes) -> Optional[dict]:

        def validate():
            if volume > cls._sample_max_volume:
                s = "Unexpected volume value: %d, expected <= %d" % (
                    volume, cls._sample_max_volume)
                logging.error(s)
                raise cls.ModuleFormatError(s)
            elif cls._sample_prefix and name.startswith(cls._sample_prefix):
                s = "Sample prefix is wrong."
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
                    "length: %d, with length: %d, offset: %d" % (repeat_length,
                                                                 length,
                                                                 repeat_offset)
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
            for i, p in enumerate(positions):
                if i >= length and p != 0:
                    s = "Non-empty positions found beyond the declared length."
                    logging.warning(s)
                    break
                elif p >= cls.patterns:
                    s = "Pattern number above allowed %d patterns " \
                        "encountered" % cls.patterns
                    logging.error(s)
                    raise cls.ModuleFormatError(s)
            if tempo == 0:
                s = "Song tempo is 0."
                logging.warning(s)

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


class UltimateSoundtracker2(UltimateSoundtracker):
    name = "Ultimate Soundtracker 2"
    description = "Ultimate Soundtracker 1.8-2.0"
    _flag_bytes = {}
    _guess_bytes = {471: b'\x78'}
    _sample_prefix = "st-"
    extensions = ("MOD", "UST", "UST2", "UST20", "UST18", "USS19")


class SoundtrackerII(UltimateSoundtracker):
    name = "Soundtracker II"
    description = "An updated version of Ultimate Soundtracker with more " \
                  "effects available"
    author = "Unknown/D.O.C."
    effects = {'ARP': 0x000, 'PORTA_DOWN': 0x100, 'PORTA_UP': 0x200,
               'VOLUME': 0xc00, 'VOL_SLIDE': 0xd00, 'VOL_AUTO_SLIDE': 0xe00}
    extensions = ("MOD", "UST", "ST")


class SoundtrackerIII(UltimateSoundtracker):
    name = "Soundtracker III"
    description = "Soundtracker III - VI file"
    author = "Scuro/Defjam/Alpha Flight/D.O.C."
    effects = {'ARP': 0x000, 'PORTA_DOWN': 0x100, 'PORTA_UP': 0x200,
               'VOLUME': 0xc00, 'VOL_SLIDE': 0xd00, 'VOL_AUTO_SLIDE': 0xe00,
               'SPEED': 0xf00}
    extensions = ("MOD", "UST", "ST")


class SoundtrackerIX(UltimateSoundtracker):
    name = "Soundtracker IX"
    description = "Soundtracker IX"
    author = "Unknown/D.O.C."
    effects = {'ARP': 0x000, 'PORTA_DOWN': 0x100, 'PORTA_UP': 0x200,
               'VOLUME': 0xc00, 'SPEED': 0xf00, 'FILTER': 0xe00}
    _flag_bytes = {}
    _guess_bytes = {471: b'\x78'}
    _sample_prefix = "st-"
    extensions = ("MOD", "UST", "ST")


class MasterSoundtracker(UltimateSoundtracker):
    name = "Master Soundtracker"
    description = "Master Soundtracker 1.0"
    author = "Tip/The New Masters"
    effects = {'ARP': 0x000, 'PORTA_DOWN': 0x100, 'PORTA_UP': 0x200,
               'VOLUME': 0xc00, 'SPEED': 0xf00, 'FILTER': 0xe00}
    _sample_max_size = 0x8000
    extensions = ("MOD", "UST", "ST", "MST")


class SoundTracker2(UltimateSoundtracker):
    name = "SoundTracker 2"
    description = "Soundtracker 2.0, 2.1, 2.2"
    author = "Unknown/D.O.C."
    effects = {'ARP': 0x000, 'PORTA_DOWN': 0x100, 'PORTA_UP': 0x200,
               'VOLUME': 0xc00, 'SPEED': 0xf00, 'FILTER': 0xe00,
               'PATTERN_BREAK': 0xd00, 'POS_JUMP': 0xb00}
    _sample_max_size = 0x8000
    extensions = ("MOD", "UST", "ST", "ST2")


class Protracker(UltimateSoundtracker):
    name = "Protracker 2"
    description = "Protracker 2.1-2.3a 31-sample module"
    author = "Unknown/D.O.C"
    samples = 31
    effects = {'ARP': 0x000, 'PORTA_UP': 0x100, 'PORTA_DOWN': 0x200,
               'PORTA_TO': 0x300, 'VIBRATO': 0x400, 'PORTA_TO+VOL_SLIDE':
                   0x500, 'VIBRATO+VOL_SLIDE': 0x600, 'TREMOLO': 0x700,
               'SAMPLE_OFFSET': 0x900, 'VOLUME_SLIDE': 0xa00, 'POS_JUMP':
                   0xb00, 'VOLUME': 0xc00, 'PATTERN_BREAK': 0xd00, 'SPEED':
                   0xf00, 'SET_FILTER': 0xe00, 'FINE_SLIDE_UP': 0xe10,
               'FINE_SLIDE_DOWN': 0xe20, 'GLISSANDO_CONTROL': 0xe30,
               'SET_VIBRATO_WAVE': 0xe40, 'SET_LOOP': 0xe5, 'JUMP_TO_LOOP':
                   0xe60, 'SET_TREMOLO_WAVE': 0xe70, 'RETRIG': 0xe90,
               'FINE_VOL_SLIDE_UP': 0xea0, 'FINE_VOL_SLIDE_DOWN': 0xeb0,
               'NOTE_CUT': 0xec0, 'NOTE_DELAY': 0xed0, 'PATTERN_DELAY': 0xee0,
               'INVERT_LOOP': 0xef}
    _sample_max_size = 0x16382
    _sample_recommended_size = 0x16382
    extensions = ("MOD", "PT")
    _flag_bytes = {1080: b'M.K.', 951: b'\x7f'}

    @classmethod
    def _generate_zero_pads(cls):
        """Called once in a metaclass to construct zero pads."""
        offset = cls._name_size - 1
        cls._zeros[offset] = b'\x00'
        offset += cls._sample_name_size
        for i in range(cls.samples):
            cls._zeros[offset] = b'\x00'
            offset += cls._sample_header_size


class NoiseTracker(Protracker):
    name = "NoiseTracker M.K."
    description = "NoiseTracker M.K. - a classic module tracker"
    author = "Mahoney & Kaktus"
    extensions = ("MOD", "NT", "NT1", "NT11", "NT10", "NT12")
    _flag_bytes = {1080: b'M.K.'}

    @classmethod
    def _generate_zero_pads(cls):
        cls._zeros = {}
