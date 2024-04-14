import io
import os
import tempfile
from typing import Literal

import ffmpeg
from pydub import AudioSegment


def convert_to_pcm(audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """
    This function converts an audio file to PCM format.

    Args:
        audio_bytes (bytes): The audio file in bytes.
        sample_rate (int, optional): The sample rate for the audio file. Default is 16000.

    Returns:
        bytes: The audio file in PCM format.
    """

    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))

    buffer = io.BytesIO()
    audio.export(buffer, format='wav', parameters=["-ar", str(sample_rate)])

    buffer.seek(0)
    wav_data = buffer.read()

    pcm_data = wav_data[44:]

    return pcm_data


def convert_to_mp3(audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """
    This function converts an audio file to MP3 format.

    Args:
        audio_bytes (bytes): The audio file in bytes.
        sample_rate (int, optional): The sample rate for the audio file. Default is 16000.

    Returns:
        bytes: The audio file in MP3 format.
    """

    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), )

    buffer = io.BytesIO()
    audio.export(buffer, format='mp3', parameters=["-ar", str(sample_rate)])

    buffer.seek(0)
    mp3_data = buffer.read()

    return mp3_data


def convert(audio_bytes: bytes, format: Literal['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'] = 'wav', **kwargs):
    """
    This function converts an audio file to the specified format.

    Args:
        audio_bytes (bytes): The audio file in bytes.
        format (str, optional): The format to convert the audio file to. Default is 'wav'.
        **kwargs: Additional parameters to pass to the ffmpeg command.

    Returns:
        bytes: The audio file in the specified format.
    """
    with tempfile.NamedTemporaryFile(suffix='.input') as input_temp:
        input_temp.write(audio_bytes)
        input_temp.flush()

        output_filename = input_temp.name + f'.{format}'

        ffmpeg.input(input_temp.name).output(
            output_filename,
            format=format,
            **kwargs
        ).run(capture_stdout=True, capture_stderr=True)

        with open(output_filename, 'rb') as f:
            output_audio_bytes = f.read()

        try:
            os.remove(output_filename)
        except OSError:
            pass

    return output_audio_bytes


__all__ = [
    "convert_to_pcm",
    "convert_to_mp3",
    "convert"
]
