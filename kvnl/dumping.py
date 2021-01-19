__all__ = (
    'dump_some', 'dumps_some',
    'dump_newline', 'dumps_newline',
    'dump_specification', 'dumps_specification',
    'dump_value', 'dumps_value',
    'dump_line', 'dumps_line',
    'dump_block', 'dumps_block',
)

from .hashing import update_hash, check_hash
from .exceptions import MalformedSpecification, Corruption, HashMismatch
from functools import wraps
from .specification import encode


def dump_some(stream, data, *, hash=None):
    if data is None:
        return
    update_hash(hash, data)
    sz = stream.write(data)
    if sz is None:
        raise BlockingIOError('[Errno 11] write could not complete without blocking')
    return sz


def dump_newline(stream, *, hash=None):
    return dump_some(stream, b'\n', hash=hash)


def dump_specification(stream, spec, *, hash=None):
    r"""dump a key specification

    Expected behavior:
    >>> dumps_specification(b'key:size')
    b'key:size='
    >>> dumps_specification(b'')
    b'='
    >>> dumps_specification(b'\n')
    b'\n'
    >>> try: dumps_specification(b'with \n inside')
    ... except MalformedSpecification as e: e
    ...
    MalformedSpecification(b'with \n inside')
    >>> try: dumps_specification(b'=')
    ... except MalformedSpecification as e: e
    ...
    MalformedSpecification(b'=')
    >>> try: dumps_specification(b'with = inside')
    ... except MalformedSpecification as e: e
    ...
    MalformedSpecification(b'with = inside')
    """
    if spec is None:
        return
    if b'=' in spec or spec != b'\n' and b'\n' in spec:
        raise MalformedSpecification(spec)
    m = dump_some(stream, spec, hash=hash)
    n = dump_some(stream, b'=', hash=hash) if spec != b'\n' else 0
    return m + n


def dump_value(stream, value, *, hash=None):
    r"""dump a value

    Expected behavior:
    >>> dumps_value(b'value')
    b'value\n'
    """
    if value is None:
        return

    value = memoryview(value).cast('b')
    m = dump_some(stream, value, hash=hash)
    n = dump_newline(stream, hash=hash)
    return m + n


def dump_line(stream, key_and_value, *, hash=None, sized=None):
    r"""dump a line

    Expected behavior:
    >>> dumps_line(('key', b'value'))
    b'key=value\n'
    >>> dumps_line('\n')
    b'\n'
    """
    if key_and_value is None:
        return

    if key_and_value == '\n':
        dump_newline(stream, hash=hash)
        return

    key, value = key_and_value

    value = memoryview(value).cast('b')

    if hash is not None and key == hash.name:
        check_hash(hash, value.decode())

    if sized is None:
        sized = len(value) > 1024 or ord(b'\n') in value
    spec = encode(key, len(value) if sized else None)

    m = dump_specification(stream, spec, hash=hash)
    n = dump_value(stream, value, hash=hash)
    return m + n


def dump_block(stream, lines, unhashed_lines=(), *, hash=None, sized=None):
    for line in lines:
        dump_line(stream, line, hash=hash, sized=sized)
    if hash is not None:
        dump_line(stream, (hash.name, hash.hexdigest().encode()), hash=None, sized=sized)
    for line in unhashed_lines:
        dump_line(stream, line, hash=None, sized=sized)
    dump_newline(stream, hash=hash)


def to_buffer(func):
    from io import BytesIO

    @wraps(func)
    def closure(*args, **kwargs):
        with BytesIO() as stream:
            func(stream, *args, **kwargs)
            return stream.getvalue()
    return closure


dumps_some = to_buffer(dump_some)
dumps_newline = to_buffer(dump_newline)
dumps_specification = to_buffer(dump_specification)
dumps_value = to_buffer(dump_value)
dumps_line = to_buffer(dump_line)
dumps_block = to_buffer(dump_block)
