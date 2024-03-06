import requests

from furchain.audio.schema import VC
from furchain.config import AudioConfig


class Sovits(VC):
    """https://github.com/svc-develop-team/so-vits-svc/blob/4.1-Stable/flask_api.py"""

    def __init__(self, speaker: str, api: str = None, pitch: int = 0,
                 auto_f0: bool = False, response_format='flac'):
        super().__init__()
        self.speaker = speaker
        self.api = api
        self.pitch = pitch
        self.auto_f0 = auto_f0
        self.response_format = response_format
        if api is None:
            api = AudioConfig.get_sovits_api()
        self.api = api

    def run(self, audio_bytes: bytes, ) -> bytes:
        data = {
            "pitch": self.pitch,
            "speaker": self.speaker,
            "auto_f0": self.auto_f0,
            "response_format": self.response_format,
        }
        files = {
            "sample": audio_bytes,
        }

        response = requests.post(self.api, data=data, files=files)
        return response.content


__all__ = [
    "Sovits"
]
