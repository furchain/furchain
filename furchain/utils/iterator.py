import queue


class BufferIterator:

    def __init__(self, buffer_size=0, stop=None):
        self.queue = queue.Queue(buffer_size)
        self.stop = stop

    def __iter__(self):
        return self

    def terminate(self):
        self.queue.put(self.stop)

    def put(self, item):
        self.queue.put(item)

    def get(self):
        return self.queue.get()

    def __next__(self):
        item = self.get()
        if item == self.stop:
            raise StopIteration
        return item
