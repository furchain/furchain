import os
import tempfile
import time

from audio_separator.separator import Separator

from furchain.audio.utils.audio_iterator import AudioIterator


class AudioSeparator:
    """
    This class is used to separate audio into different stems (vocal and instrumental) by iterating over chunks of the audio.

    Attributes:
        filename (str): The path to the audio file.
        chunk_duration (int): The duration of each chunk in seconds. Default is 10 seconds.
        separator (Separator): An instance of the Separator class used to separate the audio.
        audio_iterator (AudioIterator): An instance of the FlexibleAudioIterator class used to iterate over the audio.
    """

    def __init__(self, filename, chunk_duration=10, model_name="UVR-MDX-NET-Inst_HQ_3", flexible=True):
        """
        The constructor for the AudioSeparator class.

        Parameters: filename (str): The path to the audio file. chunk_duration (int): The duration of each chunk in
        seconds. Default is 10 seconds. Set to '-1' to disable chunk split. model_name (str): The name of the model
        to use for separation. Default is 'UVR-MDX-NET-Inst_HQ_3'.
        """
        self.filename = filename
        self.chunk_duration = chunk_duration
        self.separator = Separator(model_file_dir="/tmp/audio-separator-models/")
        self.separator.load_model(model_name=model_name)
        self.audio_iterator = AudioIterator(self.filename, self.chunk_duration)
        self.flexible = flexible

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
                if self.flexible:  # auto adjust chunk duration to provide seamless separation
                    separate_elapsed = time.time() - start_time
                    if self.chunk_duration < separate_elapsed:
                        self.audio_iterator.set_chunk_duration(int(separate_elapsed) + 1)
                with open(primary_stem_path, 'rb') as f:
                    vocal_wav = f.read()
                with open(secondary_stem_path, 'rb') as f:
                    instrumental_wav = f.read()
                os.remove(primary_stem_path)
                os.remove(secondary_stem_path)
                return vocal_wav, instrumental_wav

        raise StopIteration


__all__ = [
    "AudioSeparator"
]
