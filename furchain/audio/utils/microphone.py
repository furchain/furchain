import threading

import pyaudio


class MicrophoneStream:
    """
    This class represents a stream of audio data from a microphone.

    Attributes:
        chunk_size (int): The size of each chunk of audio data.
        format (int): The format of the audio data.
        channels (int): The number of audio channels.
        rate (int): The sample rate of the audio data.
        stop_event (threading.Event): An event that can be set to stop the stream.
    """

    def __init__(self, chunk_duration: int = 200, chunk_size=None, format=pyaudio.paInt16, channels=1, rate=16000):
        """
        The constructor for the MicrophoneStream class.

        Parameters:
            chunk_duration (int, optional): The duration of each chunk of audio data in milliseconds. Defaults to 200.
            chunk_size (int, optional): The size of each chunk of audio data. Defaults to None.
            format (int, optional): The format of the audio data. Defaults to pyaudio.paInt16.
            channels (int, optional): The number of audio channels. Defaults to 1.
            rate (int, optional): The sample rate of the audio data. Defaults to 16000.

        Raises:
            ValueError: If both chunk_size and chunk_duration are set.
        """

        # If both chunk_size and chunk_duration are set, raise an error
        if chunk_size is not None and chunk_duration is not None:
            raise ValueError("Both chunk_size and chunk_duration cannot be set")

        # If chunk_duration is set, calculate chunk_size
        if chunk_duration is None:
            chunk_duration = 200
        chunk_size = int(rate * chunk_duration / 1000)
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels
        self.rate = rate
        self.stop_event = threading.Event()  # An event that can be set to stop the stream
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
