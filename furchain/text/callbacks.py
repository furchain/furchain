import queue
from typing import List, Callable

from furchain.logger import logger


class StrChunkCallbackIterator:
    def __init__(self, iterable, callbacks: List[Callable], response_prefix='', skip=('',)):
        self.iterable = iter(iterable)
        self.callbacks = callbacks
        self.content = ''
        self.response_prefix = response_prefix
        self.skip = skip

    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            chunk = next(self.iterable)
            if isinstance(chunk, str):
                if chunk in self.skip:
                    return self.__next__()
                if self.content == '':
                    chunk = (self.response_prefix + chunk).lstrip()
                self.content += chunk
                return chunk
            else:
                if chunk.content in self.skip:
                    return self.__next__()
                if self.content == '':
                    chunk.content = (self.response_prefix + chunk.content).lstrip()
                self.content += chunk.content
                return chunk.content
        except StopIteration as e:
            for callback in self.callbacks:
                callback(self.content)
            logger.debug(f"Response: {self.content}")
            raise e


class FutureIter:
    """An iterator that retrieves items from a queue and waits for their results."""

    def __init__(self, queue: queue.Queue):
        self.queue = queue

    def __iter__(self):
        return self

    def __next__(self):
        future = self.queue.get()
        if isinstance(future, StopIteration):
            raise future
        return future.result()
