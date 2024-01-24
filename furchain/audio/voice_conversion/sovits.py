import requests

from furchain.audio.schema import ParrotVC
from furchain.config import AudioConfig


class Sovits(ParrotVC):
    """https://github.com/svc-develop-team/so-vits-svc/blob/4.1-Stable/flask_api.py"""

    default_speaker = "nahida"

    def __init__(self, api_base: str = None, **kwargs):
        super().__init__(**kwargs)
        if api_base is None:
            api_base = AudioConfig.get_sovits_api()
        self.api_base = api_base

    def run(self, flac_bytes: bytes, pitch: int = 0, speaker: str = 'nahida',
            auto_f0: bool = False, response_format='flac') -> bytes:
        data = {
            "pitch": pitch,
            "speaker": speaker,
            "auto_f0": auto_f0,
            "response_format": response_format,
        }
        files = {
            "sample": flac_bytes,
        }

        response = requests.post(self.api_base, data=data, files=files)
        return response.content
