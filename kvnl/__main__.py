#!/usr/bin/env python3

DISABLED = r'''Some lazy testing of KVNL

KVNL needs to work consistently on blocking and nonblocking streams.

We use an OS pipe to pass data around since they are file-like.
>>> from pysh import Pipe
>>> pipe = Pipe()
>>> pipe.write(b'hello'); pipe.read()
5
b'hello'

They support nonblocking I/O:
>>> pipe = Pipe()
>>> pipe.read_fd.flags.O_NONBLOCK = 1
>>> pipe.read() is None
True
>>> pipe.close()

Start with a simple wrapper around a stream's .read() method. This should be
fine with blocking I/O:
>>> from kvnl import load_some
>>> pipe = Pipe()
>>> pipe.write(b'hello')
5
>>> with pipe.read_fd.open() as stream: next(load_some(stream))
...
b'hello'

and nonblocking, too:
>>> pipe = Pipe()
>>> pipe.read_fd.flags.O_NONBLOCK = 1
>>> with pipe.read_fd.open() as stream:
...     load = load_some(stream)
...     next(load) is None
...     pipe.write(b'hello')
...     next(load)
...
True
5
b'hello'

And it should support hashing:
>>> from kvnl import new_hash
>>> pipe = Pipe()
>>> hash = new_hash('md5')
>>> pipe.write(b'hello')
5
>>> with pipe.read_fd.open() as stream: next(load_some(stream, hash=hash))
...
b'hello'
>>> hash.hexdigest()
'5d41402abc4b2a76b9719d911017c592'
>>> h = new_hash('md5'); h.update(b'hello'); h.hexdigest()
'5d41402abc4b2a76b9719d911017c592'

There is a corresponding dump_some():
>>> from kvnl import dump_some
>>> pipe = Pipe()
>>> dhash, lhash = new_hash('md5'), new_hash('md5')
>>> with pipe.write_fd.open() as stream: dump_some(stream, b'hello', hash=dhash)
...
5
>>> with pipe.read_fd.open() as stream: next(load_some(stream, hash=lhash))
...
b'hello'
>>> dhash.digest() == lhash.digest()
True

'''

from doctest import testmod

from . import hashing, loading, dumping

for mod in hashing, loading, dumping:
    testmod(mod)

testmod()
