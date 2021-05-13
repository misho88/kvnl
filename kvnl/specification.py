__all__ = 'encode', 'decode'


def check_name(key):
    if any(c in key for c in ':=\n'):
        raise ValueError(f'invalid key: {repr(tok)} in {repr(key)} is not an isidentifier')


def encode(key, size=None):
    check_name(key)
    return (key if size is None else f'{key}:{size}').encode()


def decode(spec):
    key = spec.decode('ascii')
    if ':' in key:
        key, size = key.split(':', maxsplit=1)
        size = int(size)
        if size < 0:
            raise ValueError(f'size must be nonnegative, not {size}')
    else:
        size = None
    check_name(key)
    return key, size
