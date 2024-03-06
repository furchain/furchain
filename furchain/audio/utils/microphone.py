import io
import threading

import pyaudio
import pydub


class Microphone:
    """
    This class represents a microphone that can capture audio data in chunks.

    Attributes:
        chunk_duration (int): The duration of each chunk in milliseconds. Default is 200.
        chunk_size (int): The size of each chunk in samples. If not provided, it is calculated based on the chunk duration and sample rate.
        format (int): The format of the audio data. Default is pyaudio.paInt16.
        channels (int): The number of channels. Default is 1.
        rate (int): The sample rate. Default is 16000.
        output_format (str): The format of the output audio data. Default is 'pcm'.
        stop_event (threading.Event): An event that can be set to stop the stream.
        stream (pyaudio.Stream): The audio stream.
        p (pyaudio.PyAudio): The PyAudio object.

    Methods:
        __enter__(): Opens the audio stream and returns a generator function that reads chunks of data from the microphone.
        __exit__(exc_type, exc_val, exc_tb): Stops the stream and terminates the PyAudio object.
        stop(): Sets the stop event to stop the stream.
    """

    def __init__(self, chunk_duration: int = 200, chunk_size=None, format=pyaudio.paInt16, channels=1, rate=16000,
                 output_format='pcm'):
        """
        Initializes the Microphone with the given chunk duration, chunk size, format, channels, sample rate, and output format.
        """
        if chunk_size is None:
            chunk_size = int(rate * chunk_duration / 1000)
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels
        self.output_format = output_format
        self.rate = rate
        self.stop_event = threading.Event()  # An event that can be set to stop the stream
        self.stream = None
        self.p = None

    def __enter__(self):
        """
        Opens the audio stream and returns a generator function that reads chunks of data from the microphone.
        """
        self.p = pyaudio.PyAudio()

        # Open the stream
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.chunk_size)

        def _run():
            while not self.stop_event.is_set():
                # Read a chunk of data from the microphone
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                if self.output_format == 'pcm':
                    yield data
                else:
                    buffer = io.BytesIO()
                    pydub.AudioSegment(
                        data=data,
                        sample_width=self.p.get_sample_size(self.format),
                        frame_rate=self.rate,
                        channels=self.channels,
                    ).export(buffer, format=self.output_format)
                    yield buffer.getvalue()

        return _run()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stops the stream and terminates the PyAudio object.
        """
        self.stop()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.stream = None
        self.p = None

    def stop(self):
        """
        Sets the stop event to stop the stream.
        """
        self.stop_event.set()


__all__ = [
    "Microphone"
]
