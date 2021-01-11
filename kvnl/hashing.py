__all__ = 'new_hash', 'update_hash'

import hashlib
from .exceptions import HashMismatch


def new_hash(algo, string=b''):
    """create a HASH object by name

    This is a bit easier than importing from hashlib and instantiating by hand.

    >>> h = new_hash('md5'); type(h); h.name
    <class '_hashlib.HASH'>
    'md5'
    >>> h = new_hash('sha256'); type(h); h.name
    <class '_hashlib.HASH'>
    'sha256'
    """
    try:
        return getattr(hashlib, algo)(string)
    except AttributeError as e:
        avail = ', '.join(hashlib.algorithms_available)
        raise ValueError(f'algo should be one of {avail}') from e


def update_hash(hash, data):
    if hash is not None:
        hash.update(data)


def check_hash(actual, expected):
    actual_digest = actual if isinstance(actual, str) else actual.hexdigest()
    expected_digest = expected if isinstance(expected, str) else expected.hexdigest()
    if actual_digest != expected_digest:
        raise HashMismatch(actual_digest, expected_digest)
