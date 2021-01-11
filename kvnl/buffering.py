__all__ = 'BufferReady', 'buffered'

from collections import deque


class BufferReady:
    __slots__ = ()


def buffered(iterable, report_ready=False):
    queue = deque()
    for item in iterable:
        if item is None:
            yield
        else:
            queue.append(item)
    if report_ready:
        yield BufferReady
    yield from queue
