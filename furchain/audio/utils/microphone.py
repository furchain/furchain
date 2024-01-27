import threading

import pyaudio


class MicrophoneStream:
    def __init__(self, chunk_size=1024, format=pyaudio.paInt16, channels=1, rate=16000):
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels
        self.rate = rate
        self.stop_event = threading.Event()

    def __iter__(self):
        # Initialize the PyAudio object
        p = pyaudio.PyAudio()

        # Open the stream
        stream = p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk_size)

        try:
            while not self.stop_event.is_set():
                # Read a chunk of data from the microphone
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                yield data
        finally:
            # Handle cleanup: stop the stream, close it, and terminate PyAudio
            stream.stop_stream()
            stream.close()
            p.terminate()

    def stop(self):
        self.stop_event.set()
