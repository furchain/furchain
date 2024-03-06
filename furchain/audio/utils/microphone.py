import io
import threading

import pyaudio
import pydub


class Microphone:
    """
    This class represents a stream of audio data from a microphone.

    Attributes:
        chunk_size (int): The size of each chunk of audio data.
        format (int): The format of the audio data.
        channels (int): The number of audio channels.
        rate (int): The sample rate of the audio data.
        stop_event (threading.Event): An event that can be set to stop the stream.
    """

    def __init__(self, chunk_duration: int = 200, chunk_size=None, format=pyaudio.paInt16, channels=1, rate=16000,
                 output_format='pcm'):
        """
        The constructor for the MicrophoneStream class.

        Parameters:
            chunk_duration (int, optional): The duration of each chunk of audio data in milliseconds. Defaults to 200.
            chunk_size (int, optional): The size of each chunk of audio data. Defaults to None.
            format (int, optional): The format of the audio data. Defaults to pyaudio.paInt16.
            channels (int, optional): The number of audio channels. Defaults to 1.
            rate (int, optional): The sample rate of the audio data. Defaults to 16000.
            output_format (str, optional): The format of the audio data to be yielded. Defaults to 'pcm'.

        Raises:
            ValueError: If both chunk_size and chunk_duration are set.
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
        self.stop()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.stream = None
        self.p = None

    def stop(self):
        self.stop_event.set()
