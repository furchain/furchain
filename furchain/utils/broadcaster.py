import concurrent.futures
import queue
import threading
from typing import List, Iterable


class FutureIter:
    """
    A class that wraps a queue object and provides an iterator interface.

    Attributes:
        queue (queue.Queue): The queue object to be iterated over.
    """

    def __init__(self, queue: queue.Queue):
        """
        Initializes the FutureIter instance with a queue.

        Args:
            queue (queue.Queue): The queue object to be iterated over.
        """
        self.queue = queue

    def __iter__(self):
        """
        Returns the iterator object (self).

        Returns:
            FutureIter: The iterator object.
        """
        return self

    def __next__(self):
        """
        Retrieves the next item from the queue.

        Returns:
            Any: The result of the future object.

        Raises:
            Exception: If the future object is an instance of Exception.
        """
        future = self.queue.get()
        if isinstance(future, Exception):
            raise future
        return future.result()


def iterator_callback_broadcaster(iterator: Iterable, callbacks) -> List[Iterable]:
    """
    Broadcasts the results of an iterator to multiple callbacks.

    Args:
        iterator (Iterable): The iterator to broadcast.
        callbacks (list): The list of callback functions.

    Returns:
        List[Iterable]: A list of FutureIter objects for each callback.
    """
    iterator = iter(iterator)
    broadcast = {callback: [] for callback in callbacks}
    executor = concurrent.futures.ThreadPoolExecutor()
    lock = threading.Lock()
    callback_queues = {callback: queue.Queue() for callback in callbacks}
    callback_iters = [FutureIter(callback_queues[callback]) for callback in callbacks]

    def broadcast_cache(cache):
        """
        Broadcasts cache to all callbacks.

        Args:
            cache (Any): The cache value to broadcast.
        """
        for cache_list in broadcast.values():
            cache_list.append(cache)

    def add_cache():
        """
        Adds next iterator value to cache and broadcasts it.
        """
        try:
            cache_value = next(iterator)
        except StopIteration as e:
            cache_value = e
        except Exception as e:
            cache_value = e
        broadcast_cache(cache_value)

    def callback_on_cache(callback):
        """
        Calls callback with cache values until cache is empty.

        Args:
            callback (function): The callback function to call.
        """
        while True:
            if not broadcast[callback]:
                with lock:
                    if not broadcast[callback]:
                        add_cache()
            cache_value = broadcast[callback].pop(0)
            if isinstance(cache_value, StopIteration):
                callback_queues[callback].put(cache_value)
                return
            future = executor.submit(callback, cache_value)
            callback_queues[callback].put(future)

    for callback in callbacks:
        executor.submit(callback_on_cache, callback)

    return callback_iters


__all__ = [
    "iterator_callback_broadcaster"
]
