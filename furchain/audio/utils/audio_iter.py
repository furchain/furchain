import io
import os
import tempfile
import time
from io import BytesIO

import librosa
import soundfile as sf
from audio_separator.separator import Separator
from pydub import AudioSegment

from furchain.logger import logger


class FlexibleAudioIterator:
    def __init__(self, filename, chunk_duration=10.0, sr=None):
        self.filename = filename
        self.chunk_duration = chunk_duration if chunk_duration > 0 else 2 ** 31
        self.current_pos = 0
        self.audio, self.sr = librosa.load(self.filename, sr=sr, mono=True)
        self.chunk_size = int(self.sr * self.chunk_duration)

    def __iter__(self):
        return self

    def __next__(self):
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
        self.chunk_duration = duration
        self.chunk_size = int(self.sr * self.chunk_duration)


class AudioSeparator:
    """
    This class is used to separate audio into different stems (vocal and instrumental) by iterating over chunks of the audio.

    Attributes:
        filename (str): The path to the audio file.
        chunk_duration (int): The duration of each chunk in seconds. Default is 10 seconds.
        separator (Separator): An instance of the Separator class used to separate the audio.
        audio_iterator (FlexibleAudioIterator): An instance of the FlexibleAudioIterator class used to iterate over the audio.
    """

    def __init__(self, filename, chunk_duration=10, model_name="UVR-MDX-NET-Inst_HQ_3"):
        """
        The constructor for the AudioSeparator class.

        Parameters: filename (str): The path to the audio file. chunk_duration (int): The duration of each chunk in
        seconds. Default is 10 seconds. Set to '-1' to disable chunk split. model_name (str): The name of the model
        to use for separation. Default is 'UVR-MDX-NET-Inst_HQ_3'.
        """
        self.filename = filename
        self.chunk_duration = chunk_duration
        self.separator = Separator()
        self.separator.load_model(model_name=model_name)
        self.audio_iterator = None

    def __enter__(self):
        """
        The method to make AudioSeparator a context manager. It initializes the audio_iterator.

        Returns:
            self: Returns the instance of the class.
        """
        self.audio_iterator = FlexibleAudioIterator(self.filename, self.chunk_duration)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        The method to make AudioSeparator a context manager. It cleans up the audio_iterator when exiting the context.
        """
        self.audio_iterator = None

    def __iter__(self):
        """
        The method to make AudioSeparator iterable.

        Returns:
            self: Returns the instance of the class.
        """
        return self

    def __next__(self):
        """
        The method to make AudioSeparator an iterator. It separates each chunk of audio into vocal and instrumental stems.

        Returns:
            tuple: A tuple containing the byte data of the vocal and instrumental audio.

        Raises:
            StopIteration: If the audio_iterator is not initialized or if there are no more chunks to process.
        """
        if self.audio_iterator is None:
            raise StopIteration("Audio iterator not initialized. Use 'with' statement to initialize.")

        for audio_chunk in self.audio_iterator:
            with tempfile.NamedTemporaryFile() as f:
                f.write(audio_chunk)
                start_time = time.time()
                primary_stem_path, secondary_stem_path = self.separator.separate(f.name)
                separate_elapsed = time.time() - start_time
                if self.chunk_duration < separate_elapsed:
                    self.audio_iterator.set_chunk_duration(int(separate_elapsed) + 1)
                with open(primary_stem_path, 'rb') as f:
                    vocal_audio = f.read()
                with open(secondary_stem_path, 'rb') as f:
                    instrumental_audio = f.read()
                os.remove(primary_stem_path)
                os.remove(secondary_stem_path)
                return vocal_audio, instrumental_audio

        raise StopIteration


def merge_audios(*audio_byte_streams, output_format='mp3'):
    """
    Merges multiple audio byte streams into one and outputs it in the specified format.

    :param audio_byte_streams: List of audio byte stream arguments.
    :param output_format: The desired output format (default is 'mp3').
    :return: Byte stream of the merged audio in the specified format.
    """
    # Convert the first audio byte stream to an AudioSegment
    combined = AudioSegment.from_file(BytesIO(audio_byte_streams[0]))

    # Overlay the remaining audio byte streams onto the combined AudioSegment
    for audio_bytes in audio_byte_streams[1:]:
        audio_segment = AudioSegment.from_file(BytesIO(audio_bytes))
        combined = combined.overlay(audio_segment)

    # Export the combined AudioSegment to a byte stream in WAV format
    # WAV is used as an intermediate format for compatibility
    intermediate_byte_stream = BytesIO()
    combined.export(intermediate_byte_stream, format=output_format)
    intermediate_byte_stream.seek(0)  # Reset to the start of the stream
    return intermediate_byte_stream.getvalue()
