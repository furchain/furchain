def get_format_from_magic_bytes(audio_bytes: bytes) -> str:
    """
    This function determines the format of an audio file based on its magic bytes.

    Args:
        audio_bytes (bytes): The audio file in bytes.

    Returns:
        str: The format of the audio file. If the format cannot be determined, it returns 'unknown'.
    """
    if audio_bytes.startswith(b'\xFF\xFB'):
        return 'mp3'
    elif audio_bytes.startswith(b'RIFF') and audio_bytes[8:12] == b'WAVE':
        return 'wav'
    elif audio_bytes.startswith(b'OggS'):
        if b'Opus' in audio_bytes[28:32]:
            return 'opus'
        else:
            return 'ogg'
    elif audio_bytes.startswith(b'fLaC'):
        return 'flac'
    elif audio_bytes.startswith(b'\xFF') and (audio_bytes[1] & 0xF6) == 0xF0:
        return 'aac'
    else:
        return 'unknown'


__all__ = [
    "get_format_from_magic_bytes"
]
