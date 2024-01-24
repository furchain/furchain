import io
import subprocess
import tempfile

from pydub import AudioSegment
from pydub.playback import play

from furchain.logger import logger


def get_format_from_magic_bytes(audio_bytes: bytes) -> str:
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
        logger.warning('Unknown audio format based on magic bytes, attempting to guess format')
        return 'unknown'  # We'll attempt to guess the format later


def play_audio_bytes(audio_bytes: bytes):
    try:
        format = get_format_from_magic_bytes(audio_bytes)
        if format == 'unknown':
            # If the format is unknown, let's try using a temporary file
            # and let pydub or ffmpeg guess the format
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as f:
                f.write(audio_bytes)
                f.seek(0)
                audio = AudioSegment.from_file(f.name)
        else:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)

        play(audio)
    except Exception as e:
        logger.error(f"Failed to play audio with pydub: {e}")
        # If pydub fails, try using the system's default player as a fallback
        try:
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as f:
                f.write(audio_bytes)
                f.flush()
                logger.info(f"Attempting to play audio with system's default player: {f.name}")
                if subprocess.call(
                        ['open', f.name]) != 0:  # 'open' for macOS, 'xdg-open' for Linux, 'start' for Windows
                    logger.error("Failed to play audio with system's default player.")
        except Exception as ex:
            logger.error(f"Failed to play audio with system's default player: {ex}")
