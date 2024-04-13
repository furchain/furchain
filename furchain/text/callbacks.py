from typing import List, Callable

from furchain.logger import logger


class StrChunkCallbackIterator:
    """
    This class provides an iterator over a string iterable, allowing to read the string data in chunks.

    Attributes:
        iterable (iter): The iterable to iterate over.
        callbacks (List[Callable]): The list of callback functions to call when the iteration is finished.
        content (str): The content read so far.
        skip (tuple): The chunks to skip.

    Methods:
        add_callback(callback): Adds a callback function to the list of callbacks.
        __iter__(): Returns the iterator.
        __next__(): Returns the next chunk of string data. If the end of the iterable is reached, calls the callbacks and raises StopIteration.
    """

    def __init__(self, iterable, callbacks: List[Callable], skip=tuple()):
        """
        Initializes the StrChunkCallbackIterator with the given iterable, callbacks, response prefix, and skip.
        """
        self.iterable = iter(iterable)
        self.callbacks = callbacks
        self.content = ''
        self.skip = skip

    def add_callback(self, callback: Callable):
        """
        Adds a callback function to the list of callbacks.

        Args:
            callback (Callable): The callback function to add.
        """
        self.callbacks.append(callback)

    def __iter__(self):
        """
        Returns the iterator.
        """
        return self

    def __next__(self):
        """
        Returns the next chunk of string data. If the end of the iterable is reached, calls the callbacks and raises StopIteration.
        """
        try:
            chunk = next(self.iterable)
            if isinstance(chunk, str):
                if chunk in self.skip:
                    return self.__next__()
                self.content += chunk
                return chunk
            else:
                if chunk.content in self.skip:
                    return self.__next__()
                self.content += chunk.content
                return chunk.content
        except StopIteration as e:
            for callback in self.callbacks:
                callback(self.content)
            logger.debug(f"Response: {self.content}")
            raise e


__all__ = [
    "StrChunkCallbackIterator"
]
