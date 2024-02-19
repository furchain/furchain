import concurrent.futures
import queue
import threading
from typing import List, Iterable


class FutureIter:
    """An iterator that retrieves items from a queue and waits for their results."""

    def __init__(self, queue: queue.Queue):
        self.queue = queue

    def __iter__(self):
        return self

    def __next__(self):
        future = self.queue.get()
        if isinstance(future, Exception):
            raise future
        return future.result()


def iterator_callback_broadcaster(iterator: Iterable, callbacks) -> List[Iterable]:
    """Broadcasts the elements of an iterator to multiple callback functions concurrently."""
    iterator = iter(iterator)
    broadcast = {callback: [] for callback in callbacks}
    executor = concurrent.futures.ThreadPoolExecutor()
    lock = threading.Lock()
    callback_queues = {callback: queue.Queue() for callback in callbacks}
    callback_iters = [FutureIter(callback_queues[callback]) for callback in callbacks]

    def broadcast_cache(cache):
        """Broadcasts cache to all callbacks."""
        for cache_list in broadcast.values():
            cache_list.append(cache)

    def add_cache():
        """Adds next iterator value to cache and broadcasts it."""
        try:
            cache_value = next(iterator)
        except StopIteration as e:
            cache_value = e
        except Exception as e:
            cache_value = e
        broadcast_cache(cache_value)

    def call_cache_on_callback(callback):
        """Calls callback with cache values until cache is empty."""
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
        executor.submit(call_cache_on_callback, callback)

    return callback_iters
