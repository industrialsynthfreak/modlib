class ModuleFormatMeta(type):
    """Prepares and registers module formats."""

    formats = set()

    def __new__(mcs, name, bases, attributes):
        new_cls = super().__new__(mcs, name, bases, attributes)
        if hasattr(new_cls, 'extensions'):
            new_cls.extensions = tuple([ext.upper() for ext in
                                        new_cls.extensions])
        if hasattr(new_cls, '_generate_zero_pads'):
            new_cls._generate_zero_pads()
        mcs.formats.add(new_cls)
        return new_cls
