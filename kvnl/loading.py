__all__ = (
    'load_some', 'loads_some',
    #'load_until_newline', 'loads_until_newline',
    'load_specification', 'loads_specification',
    'load_value', 'loads_value',
    'load_line', 'loads_line',
    'load_block', 'loads_block',
)


from .exceptions import MalformedSpecification, Corruption, HashMismatch
from functools import wraps
from .hashing import update_hash, new_hash, check_hash  # noqa: F401
from .specification import decode


def load_some(stream, size=None, delim=None, *, hash=None):
    r"""load some data from a stream

    Expected behavior:
    >>> next(loads_some(b'data', 4))
    b'data'
    >>> payload = b'data'
    >>> h = new_hash('md5'); next(loads_some(payload, 4, hash=h)); h.digest() == new_hash('md5', payload).digest()
    b'data'
    True
    >>> class NonblockingFile:
    ...     def readinto(n=None):
    ...         return
    ...
    >>> next(load_some(NonblockingFile, 1)) is None
    True
    """
    if size is not None and (not isinstance(size, int) or size < 0):
        raise ValueError(f'size must be positive int, not {repr(size)}')
    if delim is not None:
        if not isinstance(delim, (list, tuple)):
            delim = delim,
        delim = tuple(memoryview(d).tobytes() for d in delim)
        for d in delim:
            if len(d) == 0:
                raise ValueError(f'deliminators must be bytes of nonzero length, not {repr(d)}')

    request_size = 1 if delim is not None else size
    initial_size = size if size is not None else 1024

    if request_size is None:
        request_size = initial_size

    buff = bytearray(initial_size)
    view = memoryview(buff)
    pos = 0
    while True:
        end = pos + request_size
        if end > len(buff):
            del view  # buffer cannot be resized while view exists
            buff += b'0' * initial_size
            view = memoryview(buff)

        piece_size = stream.readinto(view[pos:end])
        if piece_size is None:
            yield
            continue
        pos += piece_size
        if piece_size == 0:
            if (size is None or size == 0) and delim is None:
                break
            else:
                raise EOFError
        if size is not None:
            request_size = min(request_size, size - pos)
        if not request_size:
            break
        if delim is not None and any(view[pos - len(d):pos].tobytes() == d for d in delim):
            break
    result = view[:pos].tobytes()
    update_hash(hash, result)
    yield result
    return


def load_specification(stream, *, hash=None):
    r"""load the specification part of the line (key and size)

    Expected behavior:
    >>> next(loads_specification(b'key:12=...'))
    b'key:12'
    >>> next(loads_specification(b'\n'))
    b'\n'
    >>> next(loads_specification(b'='))
    b''
    >>> try: next(loads_specification(b''))
    ... except EOFError as e: e
    ...
    EOFError()
    >>> try: next(loads_specification(b'a\n='))
    ... except MalformedSpecification as e: e
    ...
    MalformedSpecification(b'a\n')
    >>> payload = b'key='
    >>> h = new_hash('md5'); next(loads_specification(payload, hash=h)); h.digest() == new_hash('md5', payload).digest()
    b'key'
    True
    >>> class NonblockingFile:
    ...     def readinto(n=None):
    ...         return
    ...
    >>> next(load_specification(NonblockingFile)) is None
    True
    """
    for item in load_some(stream, delim=(b'=', b'\n'), hash=hash):
        if item is None:
            yield
    if item.endswith(b'='):
        yield item[:-1]
    elif item == b'\n':
        yield item
    else:
        raise MalformedSpecification(item)


def load_value(stream, size=None, *, hash=None):
    r"""load the value part of the line

    Expected behavior:
    >>> next(loads_value(b'value\n'))
    b'value'
    >>> next(loads_value(b'value with \n in it\n', 18))
    b'value with \n in it'
    >>> try: next(x for x in loads_value(b'value') if x is not None)
    ... except EOFError as e: e
    ...
    EOFError()
    >>> payload, size = b'value\n', None
    >>> h = new_hash('md5'); next(loads_value(payload, hash=h)); h.digest() == new_hash('md5', payload).digest()
    b'value'
    True
    >>> payload, size = b'value\n', 5
    >>> h = new_hash('md5'); next(loads_value(payload, hash=h)); h.digest() == new_hash('md5', payload).digest()
    b'value'
    True
    >>> class NonblockingFile:
    ...     def readinto(n=None):
    ...         return
    ...
    >>> next(load_value(NonblockingFile)) is None
    True
    """

    if size is not None:
        for value in load_some(stream, size, hash=hash):
            if value is None:
                yield
        if len(value) != size:
            raise Corruption(f'expected {size} bytes in value, got {len(value)}')
        for rest in load_some(stream, delim=b'\n', hash=hash):
            if rest is None:
                yield
        if rest != b'\n':
            raise Corruption(f'got {len(rest) - 1} extra bytes in value')
    else:
        for value in load_some(stream, delim=b'\n', hash=hash):
            if value is None:
                yield
        value = value[:-1]
    yield value


def load_line(stream, *, hash=None):
    r"""load a line

    Expected behavior:
    >>> next(loads_line(b'key=value\n'))
    ('key', b'value')
    >>> next(loads_line(b'key:5=value\n'))
    ('key', b'value')
    >>> next(loads_line(b'\n'))
    '\n'
    >>> payload = b'key=value\n'
    >>> h = new_hash('md5'); next(loads_line(payload, hash=h)); h.digest() == new_hash('md5', payload).digest()
    ('key', b'value')
    True
    >>> class NonblockingFile:
    ...     def readinto(n=None):
    ...         return
    ...
    >>> next(load_value(NonblockingFile)) is None
    True
    """
    actual_digest = None if hash is None else hash.hexdigest()

    for spec in load_specification(stream, hash=hash):
        if spec is None:
            yield

    if spec == b'\n':
        yield '\n'
        return

    try:
        key, size = decode(spec)
    except (UnicodeDecodeError, ValueError) as e:
        raise Corruption(*e.args) from e

    for value in load_value(stream, size, hash=hash):
        if value is None:
            yield

    if hash is not None and key == hash.name:
        check_hash(actual_digest, value.decode())
    yield key, value


def load_block(stream, *, hash=None):
    while True:
        for subsection in load_line(stream, hash=hash):
            if subsection is None:
                yield
        if subsection == '\n':
            return
        yield subsection


def from_buffer(func):
    from io import BytesIO

    @wraps(func)
    def closure(data, *args, **kwargs):
        with BytesIO(data) as stream:
            yield from func(stream, *args, **kwargs)
    return closure


loads_some = from_buffer(load_some)
loads_specification = from_buffer(load_specification)
loads_value = from_buffer(load_value)
loads_line = from_buffer(load_line)
loads_block = from_buffer(load_block)
