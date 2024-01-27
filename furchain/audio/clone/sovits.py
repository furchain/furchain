import requests

from furchain.audio.schema import ParrotVC
from furchain.config import AudioConfig


class Sovits(ParrotVC):
    """https://github.com/svc-develop-team/so-vits-svc/blob/4.1-Stable/flask_api.py"""

    default_speaker = "nahida"

    def __init__(self, api: str = None, **kwargs):
        super().__init__(**kwargs)
        if api is None:
            api = AudioConfig.get_sovits_api()
        self.api = api

    def run(self, audio_bytes: bytes, pitch: int = 0, speaker: str = 'nahida',
            auto_f0: bool = False, response_format='flac') -> bytes:
        data = {
            "pitch": pitch,
            "speaker": speaker,
            "auto_f0": auto_f0,
            "response_format": response_format,
        }
        files = {
            "sample": audio_bytes,
        }

        response = requests.post(self.api, data=data, files=files)
        return response.content
