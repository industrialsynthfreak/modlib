import logging


class ModuleFormat:
    name = 'Module Format Abstract Class'
    encoding = 'ascii'
    extensions = tuple()
    _zeros = dict()
    _flag_bytes = dict()
    _guess_bytes = dict()

    class ModuleFormatError(RuntimeError):
        """This error is risen when module file violates validation on load."""

    @classmethod
    def decode_string(cls, data: bytes) -> str:
        return data.rstrip(b'\x00').decode(cls.encoding)

    @classmethod
    def validate_extension(cls, name: str, extension: str) -> bool:
        """Checks for Amiga format first (no extension and extension prefix
        at the file start. The validation is not case-sensitive, because it
        seems reasonable."""
        logging.debug("Validating extension for %s format" % cls.name)
        name = name.upper()
        extension = extension.upper()
        if extension == "":
            for ext in cls.extensions:
                if name.upper().startswith(ext.upper()):
                    logging.debug("OK")
                    return True
        elif extension.upper() in cls.extensions:
            logging.debug("OK")
            return True
        logging.error("Extension %s not recognized" % extension)
        return False

    @classmethod
    def _validate_bytes(cls, data: bytes, sequence: dict) -> bool:
        """Validates a sequence of flag bytes / zero pads / etc. Sequence
        should be provided as dict of offset: bytestring values."""
        try:
            for offset, b in sequence.items():
                if data[offset:offset + len(b)] != b:
                    s = "Wrong byte value at offset %d, expected %s" % (
                        offset, b)
                    logging.error(s)
                    return False
        except IndexError:
            s = "End of file reached."
            logging.error(s)
            return False
        else:
            logging.debug("OK")
            return True

    @classmethod
    def validate(cls, data: bytes, validation_level=0) -> bool:
        if validation_level == 0:
            s = "Flag bytes validation"
            logging.debug(s)
            return cls._validate_bytes(data, cls._flag_bytes)
        elif validation_level == 1:
            s = "Zero pads validation"
            logging.debug(s)
            return cls._validate_bytes(data, cls._zeros)
        else:
            s = "Some common bytes validation"
            logging.debug(s)
            return cls._validate_bytes(data, cls._guess_bytes)
