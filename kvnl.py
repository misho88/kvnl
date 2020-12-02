r"""KVNL - simple, ascii-based serialization"""

__all__ = (
    'get_hash',
    'dump_empty_line', 'dumps_empty_line',
    'dump_line', 'dumps_line', 'load_line', 'loads_line',
    'dump_lines', 'dumps_lines', 'load_lines', 'loads_lines',
    'dump_block', 'dumps_block', 'load_block', 'loads_block',
)


def get_hash(algo):
    """create a HASH object easily

    This is a bit easier than importing from hashlib and instantiating by hand.

    >>> h = get_hash('md5'); type(h); h.name
    <class '_hashlib.HASH'>
    'md5'
    >>> h = get_hash('sha256'); type(h); h.name
    <class '_hashlib.HASH'>
    'sha256'
    """

    import hashlib
    try:
        return getattr(hashlib, algo)()
    except AttributeError as e:
        avail = ', '.join(hashlib.algorithms_available)
        raise ValueError(f'algo should be one of {avail}') from e


def dumps_helper(func: callable, *args, **kwargs):
    from io import BytesIO
    with BytesIO() as stream:
        func(stream, *args, **kwargs)
        return stream.getvalue()


def loads_helper(func: callable, data, *args, **kwargs):
    from io import BytesIO
    with BytesIO(data) as stream:
        return func(stream, *args, **kwargs)


def loads_helper2(func: callable, data, *args, **kwargs):
    from io import BytesIO
    with BytesIO(data) as stream:
        yield from func(stream, *args, **kwargs)


def dump_empty_line(stream):
    stream.write(b'\n')


def dumps_empty_line():
    return b'\n'


def dump_line(stream, key: str, value: memoryview, sized=None, hash=None):
    """dump one line to stream"""
    if not key.isidentifier():
        raise ValueError(f'not a valid key: {key}')
    key = key.encode('ascii')
    if sized is None:
        sized = b'\n' in value
    size = f':{len(value)}'.encode() if sized else b''
    data = key, size, b'=', value, b'\n'
    if hash is not None:
        for datum in data:
            hash.update(datum)
    stream.writelines(data)


def dumps_line(key: str, value: memoryview, sized=None, hash=None):
    r"""dump one line to a bytes-like object

    >>> dumps_line('name', b'data')
    b'name=data\n'
    >>> dumps_line('name', b'multi\nline\ndata')
    b'name:15=multi\nline\ndata\n'
    >>> dumps_line('name', b'data', sized=True)
    b'name:4=data\n'
    >>> hash = get_hash('md5'); dumps_line('name', b'data', hash=hash); hash.hexdigest()
    b'name=data\n'
    'ef41daf35fdb78acaa57d166c1b0bb30'
    >>> hash = get_hash('md5'); hash.update(b'name=data\n'); hash.hexdigest()
    'ef41daf35fdb78acaa57d166c1b0bb30'
    """
    return dumps_helper(dump_line, key, value, sized, hash)


def load_line(stream, hash=None):
    """load one line from a stream"""
    err = EOFError
    keyspec = bytearray()
    while True:
        char = stream.read(1)
        if len(char) == 0:
            raise err
        if char == b'\n':
            return None
        if char != b'=':
            keyspec.append(ord(char))
        else:
            break
        err = SyntaxError
    key = keyspec.decode('ascii')
    if ':' in key:
        key, size = key.split(':', maxsplit=1)
        size = int(size)
        if size < 0:
            raise SyntaxError
    else:
        size = None

    if size is None:
        value = stream.readline().rstrip(b'\n')
    else:
        value = stream.read(size)
        if len(value) != size:
            raise SyntaxError
        newline = stream.readline()
        if newline != b'\n':
            raise SyntaxError

    if hash is not None:
        if key == hash.name:
            digest = hash.hexdigest().encode()
            if digest != value:
                raise ValueError(f'hash mismatch: expected {value}, got {digest}')
        else:
            data = keyspec, b'=', value, b'\n'
            for datum in data:
                hash.update(datum)

    return key, value


def loads_line(data: memoryview, hash=None):
    r"""load one line from a bytes-like object

    empty lines map to None:
    >>> print(loads_line(b'\n'))
    None

    otherwise, it's the inverse of dumps_line:
    >>> loads_line(b'name=data\n')
    ('name', b'data')
    >>> loads_line(b'name:15=multi\nline\ndata\n')
    ('name', b'multi\nline\ndata')

    hashing works the same way:
    >>> hash = get_hash('md5'); loads_line(b'name=data\n', hash=hash); hash.hexdigest()
    ('name', b'data')
    'ef41daf35fdb78acaa57d166c1b0bb30'

    except that if the key is the hash name, it gets validated instead of updating the hash:
    >>> hash = get_hash('md5'); loads_line(b'name=data\n', hash=hash); loads_line(b'md5=ef41daf35fdb78acaa57d166c1b0bb30\n', hash=hash);
    ('name', b'data')
    ('md5', b'ef41daf35fdb78acaa57d166c1b0bb30')
    >>> try:
    ...     hash = get_hash('md5'); loads_line(b'name=data\n', hash=hash); loads_line(b'md5=ef41daf35fdb78acaa57d166c1b0bb39\n', hash=hash);
    ... except Exception as e:
    ...     print(e)
    ...
    ('name', b'data')
    hash mismatch: expected b'ef41daf35fdb78acaa57d166c1b0bb39', got b'ef41daf35fdb78acaa57d166c1b0bb30'
    """
    return loads_helper(load_line, data, hash)


def dump_lines(stream, items, sized=None, hash=None):
    """dump several lines to stream"""
    for key, value in items:
        dump_line(stream, key, value, sized, hash)


def dumps_lines(items, sized=None, hash=None):
    r"""dump several lines to bytes-like object


    >>> dumps_lines(dict(a=b'hello', c=b'world').items())
    b'a=hello\nc=world\n'
    """
    return dumps_helper(dump_lines, items, sized, hash)


def load_lines(stream, hash=None, eof_okay=True):
    """load several lines from stream

    stops when it hits an empty line

    if oef_okay=True (default), hitting EOF does not raise an error.
    """
    try:
        while True:
            data = load_line(stream, hash)
            if data is None:
                break
            yield data
    except EOFError:
        if not eof_okay:
            raise


def loads_lines(data: memoryview, hash=None, eof_okay=True):
    r"""load several lines from bytes-like object

    >>> dict(loads_lines(b'a=hello\nc=world\n'))
    {'a': b'hello', 'c': b'world'}
    """
    return loads_helper2(load_lines, data, hash, eof_okay)


def dump_block(stream, items, sized=None, hash=None, unhashed_items=None):
    """dump a block of data to a stream"""
    if isinstance(hash, str):
        hash = get_hash(hash)
    dump_lines(stream, items, sized, hash)
    if hash is not None:
        dump_line(stream, hash.name, hash.hexdigest().encode())
    if unhashed_items is not None:
        dump_lines(stream, unhashed_items, sized)
    stream.write(b'\n')


def dumps_block(items, sized=None, hash=None, unhashed_items=None):
    r"""dump a block of data to a bytes-like object

    >>> dumps_block(dict(a=b'hello', c=b'world').items(), hash='md5')
    b'a=hello\nc=world\nmd5=c5133712016d519e3b899e1db0fe7652\n\n'

    unhashed_items don't affect the hash
    >>> dumps_block(dict(a=b'hello', c=b'world').items(), hash='md5', unhashed_items=dict(x=b'unhashed').items
    ())
    b'a=hello\nc=world\nmd5=c5133712016d519e3b899e1db0fe7652\nx=unhashed\n\n'
    """
    return dumps_helper(dump_block, items, sized, hash, unhashed_items)


def load_block(stream, hash=None, return_hash=False):
    """load a block of data from a stream"""
    if isinstance(hash, str):
        hash = get_hash(hash)
    for key, value in load_lines(stream, hash, False):
        is_hash = hash is not None and key == hash.name
        if is_hash:
            hash = None
        if return_hash or not is_hash:
            yield key, value


def loads_block(data: memoryview, hash=None, return_hash=False):
    r"""load a block of data from a bytes-like object

    >>> dict(loads_block(b'a=hello\nc=world\nmd5=c5133712016d519e3b899e1db0fe7652\n\n', hash='md5'))
    {'a': b'hello', 'c': b'world'}

    With return_hash=True, also returns the hash. Otherwise, it skips it:
    >>> dict(loads_block(b'a=hello\nc=world\nmd5=c5133712016d519e3b899e1db0fe7652\n\n', hash='md5', return_has
    h=True))
    {'a': b'hello', 'c': b'world', 'md5': b'c5133712016d519e3b899e1db0fe7652'}
    """
    return loads_helper2(load_block, data, hash, return_hash)


if __name__ == '__main__':
    from doctest import testmod
    testmod()
