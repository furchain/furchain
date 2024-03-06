import io

from pydub import AudioSegment

from furchain.audio.utils.get_format import get_format_from_magic_bytes


class AudioEditor:

    @staticmethod
    def merge(*audio_bytes_streams, output_format=None):
        """
        Merges multiple audio byte streams into one and outputs it in the specified format.

        :param audio_bytes_streams: List of audio byte stream arguments.
        :param output_format: The desired output format (default is 'mp3').
        :return: Byte stream of the merged audio in the specified format.
        """
        if output_format is None:
            output_format = get_format_from_magic_bytes(audio_bytes_streams[0])
        # Convert the first audio byte stream to an AudioSegment
        combined = AudioSegment.from_file(io.BytesIO(audio_bytes_streams[0]))

        # Overlay the remaining audio byte streams onto the combined AudioSegment
        for audio_bytes in audio_bytes_streams[1:]:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            combined = combined.overlay(audio_segment)

        # Export the combined AudioSegment to a byte stream in WAV format
        # WAV is used as an intermediate format for compatibility
        intermediate_byte_stream = io.BytesIO()
        combined.export(intermediate_byte_stream, format=output_format)
        intermediate_byte_stream.seek(0)  # Reset to the start of the stream
        return intermediate_byte_stream.getvalue()

    @staticmethod
    def concat(*audio_bytes_streams, output_format=None):
        # Create an empty AudioSegment object
        if output_format is None:
            output_format = get_format_from_magic_bytes(audio_bytes_streams[0])
        combined = AudioSegment.empty()

        # Loop through the list of audio byte data
        for audio_bytes in audio_bytes_streams:
            # Create an AudioSegment from the byte data
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            # Concatenate the audio segments
            combined += audio_segment

        # Export the combined AudioSegment to the desired format
        # and return the byte data
        buffer = io.BytesIO()
        combined.export(buffer, format=output_format)
        return buffer.getvalue()
