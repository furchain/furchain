import io

import librosa
import soundfile as sf

from furchain.logger import logger


class AudioIterator:
    """
    This class provides an iterator over an audio file, allowing to read the audio data in chunks.

    Attributes:
        filename (str): The path to the audio file.
        chunk_duration (float): The duration of each chunk in seconds. Default is 10.0.
        sr (int, optional): The sample rate for the audio file. If not provided, it is inferred from the audio file.
        current_pos (int): The current position in the audio file.
        audio (np.ndarray): The audio data.
        chunk_size (int): The size of each chunk in samples.

    Methods:
        __iter__(): Returns the iterator.
        __next__(): Returns the next chunk of audio data.
        read(duration): Reads a segment of the audio file with the given duration.
        set_chunk_duration(duration): Sets the chunk duration.
    """

    def __init__(self, filename, chunk_duration=10.0, sr=None):
        """
        Initializes the AudioIterator with the given filename, chunk duration, and sample rate.
        """
        self.filename = filename
        self.chunk_duration = chunk_duration if chunk_duration > 0 else 2 ** 31
        self.current_pos = 0
        self.audio, self.sr = librosa.load(self.filename, sr=sr, mono=True)
        self.chunk_size = int(self.sr * self.chunk_duration)

    def __iter__(self):
        """
        Returns the iterator.
        """
        return self

    def __next__(self):
        """
        Returns the next chunk of audio data. If the end of the audio file is reached, raises StopIteration.
        """
        if self.audio is None:
            raise StopIteration("Audio file not loaded. Use 'with' statement or manually call 'load_audio'.")

        if self.current_pos >= len(self.audio):
            raise StopIteration
        try:

            chunk = self.audio[self.current_pos:self.current_pos + self.chunk_size]
            self.current_pos += self.chunk_size

            with io.BytesIO() as bytes_io:
                sf.write(file=bytes_io, data=chunk, samplerate=self.sr, format='WAV', subtype='PCM_16')
                bytes_io.seek(0)
                bytes_data = bytes_io.read()
                return bytes_data
        except Exception as e:
            logger.exception(e)
            raise StopIteration(e)

    def read(self, duration):
        """
        Reads a segment of the audio file with the given duration.

        Args:
            duration (float): The duration of the segment in seconds.

        Returns:
            bytes: The audio data in bytes.
            bool: Whether the end of the audio file is reached.
        """
        if self.audio is None:
            raise ValueError("Audio file not loaded. Use 'with' statement or manually call 'load_audio'.")

        num_samples = int(self.sr * duration)
        segment = self.audio[self.current_pos:self.current_pos + num_samples]
        self.current_pos += num_samples

        if len(segment) < num_samples:
            if self.current_pos >= len(self.audio):
                end_of_audio = True
            else:
                raise ValueError("Requested duration extends beyond the available audio data.")
        else:
            end_of_audio = False

        with io.BytesIO() as bytes_io:
            sf.write(file=bytes_io, data=segment, samplerate=self.sr, format='WAV', subtype='PCM_16')
            bytes_io.seek(0)
            bytes_data = bytes_io.read()

        return bytes_data, end_of_audio

    def set_chunk_duration(self, duration):
        """
        Sets the chunk duration.

        Args:
            duration (float): The new chunk duration in seconds.
        """
        self.chunk_duration = duration
        self.chunk_size = int(self.sr * self.chunk_duration)


__all__ = [
    "AudioIterator"
]
