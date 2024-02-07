import os
import tempfile
import time
from io import BytesIO

from audio_separator.separator import Separator
from pydub import AudioSegment

from furchain.audio.utils.audio_iter import FlexibleAudioIterator


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
        self.audio_iterator = FlexibleAudioIterator(self.filename, self.chunk_duration)

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

    @staticmethod
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
