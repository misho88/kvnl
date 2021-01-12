__all__ = (
    'BaseStream', 'BufferedBaseStream',
    'LoadingStream', 'BufferedLoadingStream',
    'DumpingStream',
    'Stream', 'BufferedStream',
)

from . import loading, dumping
from .hashing import new_hash
from .buffering import buffered
from functools import wraps


def make_method(func):
    @wraps(func)
    def method(self, *args, **kwargs):
        return func(self.stream, *args, hash=self.hash, **kwargs)
    return method


def make_buffered_method(func):
    @wraps(func)
    def method(self, *args, **kwargs):
        return buffered(func(self.stream, *args, hash=self.hash, **kwargs), report_ready=self.report_ready)
    return method


def iterate(mapping, prefix, func):
    return (
        (name, func(item))
        for name, item in mapping.items()
        if name.startswith(prefix)
    )


class BaseStream:
    def __init__(self, stream, hash=None):
        self.stream = stream
        self.hash = new_hash(hash) if hash is not None else None

    def reset_hash(self):
        self.hash = new_hash(self.hash.name) if self.hash is not None else None


class BufferedBaseStream(BaseStream):
    def __init__(self, stream, hash=None, report_ready=False):
        super().__init__(stream, hash=hash)
        self.report_ready = report_ready


class LoadingMixIn:
    def load(self, include_hash=False):
        self.reset_hash()
        for line in self.load_block():
            if self.hash is not None and isinstance(line, tuple) and line[0] == self.hash.name:
                continue
            yield line
    locals().update(iterate(vars(loading), 'load_', make_method))


class BufferedLoadingMixIn(LoadingMixIn):
    locals().update(iterate(vars(loading), 'load_', make_buffered_method))


class DumpingMixIn:
    def dump(self, lines, unhashed_lines=()):
        self.reset_hash()
        return self.dump_block(lines, unhashed_lines)

    locals().update(iterate(vars(dumping), 'dump_', make_method))


class LoadingStream(BaseStream, LoadingMixIn):
    pass


class BufferedLoadingStream(BufferedBaseStream, BufferedLoadingMixIn):
    pass


class DumpingStream(BaseStream, DumpingMixIn):
    pass


class Stream(BaseStream, LoadingMixIn, DumpingMixIn):
    pass


class BufferedStream(BufferedBaseStream, BufferedLoadingMixIn, DumpingMixIn):
    pass
