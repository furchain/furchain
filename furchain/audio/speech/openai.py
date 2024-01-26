from typing import Literal

import openai

from furchain.audio.schema import ParrotTTS


class OpenaiTTS(ParrotTTS):
    default_speaker = "echo"

    @classmethod
    def run(cls, text: str, speaker: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "echo",
            response_format: Literal["mp3", "opus", "aac", "flac"] = 'mp3',
            model: Literal["tts-1", "tts-1-hd"] = 'tts-1') -> bytes:
        response = openai.audio.speech.create(
            input=text,
            voice=speaker,
            model=model,
            response_format=response_format
        )
        return response.content
