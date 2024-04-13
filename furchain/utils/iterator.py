import queue


class BufferIterator:
    """
    A class that provides an iterator interface for a buffer.

    Attributes:
        queue (queue.Queue): The queue object to be iterated over.
        stop (Any): The sentinel value that indicates the end of the iteration.

    Methods:
        terminate(): Adds the stop value to the queue to end the iteration.
        put(item): Adds an item to the queue.
        get(): Retrieves an item from the queue.
    """

    def __init__(self, buffer_size=0, stop=None):
        """
        Initializes the BufferIterator instance with a buffer size and a stop value.

        Args:
            buffer_size (int, optional): The maximum size of the buffer. Defaults to 0.
            stop (Any, optional): The sentinel value that indicates the end of the iteration. Defaults to None.
        """
        self.queue = queue.Queue(buffer_size)
        self.stop = stop

    def __iter__(self):
        """
        Returns the iterator object (self).

        Returns:
            BufferIterator: The iterator object.
        """
        return self

    def terminate(self):
        """
        Adds the stop value to the queue to end the iteration.
        """
        self.queue.put(self.stop)

    def put(self, item):
        """
        Adds an item to the queue.

        Args:
            item (Any): The item to be added to the queue.
        """
        self.queue.put(item)

    def get(self):
        """
        Retrieves an item from the queue.

        Returns:
            Any: The item retrieved from the queue.
        """
        return self.queue.get()

    def __next__(self):
        """
        Retrieves the next item from the queue.

        Returns:
            Any: The next item in the queue.

        Raises:
            StopIteration: If the next item is the stop value.
        """
        item = self.get()
        if item == self.stop:
            raise StopIteration
        return item


__all__ = [
    "BufferIterator"
]
