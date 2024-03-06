import io
import os
import tempfile
from typing import Literal

import ffmpeg
from pydub import AudioSegment

from furchain.audio.utils.play import get_format_from_magic_bytes


def convert_to_pcm(audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
    audio_format = get_format_from_magic_bytes(audio_bytes)

    # If the format could not be determined, raise an error
    if audio_format == 'unknown':
        raise ValueError("Unknown audio format. Cannot convert to PCM.")

    # Read the audio data into an AudioSegment
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format)

    # Export the audio data to a WAV file (in memory)
    buffer = io.BytesIO()
    audio.export(buffer, format='wav', parameters=["-ar", str(sample_rate)])

    # Get the buffer content
    buffer.seek(0)
    wav_data = buffer.read()

    # Extract PCM data from the WAV container (skip the 44-byte header)
    pcm_data = wav_data[44:]

    return pcm_data


def convert_to_mp3(audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
    audio_format = get_format_from_magic_bytes(audio_bytes)

    if audio_format == 'unknown':
        raise ValueError("Unknown audio format. Cannot convert to MP3.")

    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format)

    buffer = io.BytesIO()
    audio.export(buffer, format='mp3', parameters=["-ar", str(sample_rate)])

    buffer.seek(0)
    mp3_data = buffer.read()

    return mp3_data


def convert(audio_bytes: bytes, format: Literal['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'] = 'wav', **kwargs):
    """
    Convert the input audio bytes to the specified format using ffmpeg.

    Parameters:
    audio_bytes (bytes): The input audio data as bytes.
    format (str): The target format for the audio conversion. Supported formats are 'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'. Default is 'wav'.
    **kwargs: Additional keyword arguments to be passed to the ffmpeg output function.

    Returns:
    bytes: The converted audio data as bytes.
    """

    with tempfile.NamedTemporaryFile(suffix='.input') as input_temp:
        # Write the input audio bytes to the temporary file
        input_temp.write(audio_bytes)
        input_temp.flush()  # Ensure all data is written to disk

        # Create a temporary file for the output audio
        output_filename = input_temp.name + f'.{format}'

        # Use ffmpeg to convert the audio to the target format and sample rate
        ffmpeg.input(input_temp.name).output(
            output_filename,
            format=format,
            **kwargs
        ).run(capture_stdout=True, capture_stderr=True)

        # Read the converted audio bytes from the output temporary file
        with open(output_filename, 'rb') as f:
            output_audio_bytes = f.read()

        # Clean up the output temporary file
        try:
            os.remove(output_filename)
        except OSError:
            pass

    return output_audio_bytes
