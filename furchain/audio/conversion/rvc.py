import requests

from furchain.audio.schema import VC
from furchain.config import AudioConfig


class RVC(VC):
    """https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/pull/1614"""

    def __init__(self, speaker: str, api: str = None, index_path: str = None, f0up_key: int = 0,
                 f0method: str = "rmvpe", index_rate: float = 0.66, device: str = None,
                 is_half: bool = False, filter_radius: int = 3, resample_sr: int = 0,
                 rms_mix_rate: float = 1, protect: float = 0.33):
        super().__init__()
        self.speaker = speaker
        self.api = api
        self.index_path = index_path
        self.f0up_key = f0up_key
        self.f0method = f0method
        self.index_rate = index_rate
        self.device = device
        self.is_half = is_half
        self.filter_radius = filter_radius
        self.resample_sr = resample_sr
        self.rms_mix_rate = rms_mix_rate
        self.protect = protect
        if api is None:
            api = AudioConfig.get_rvc_api()
        self.api = api

    def run(self, audio_bytes: bytes) -> bytes:
        data = {
            "speaker": self.speaker,
            "index_path": self.index_path,
            "f0up_key": self.f0up_key,
            "f0method": self.f0method,
            "index_rate": self.index_rate,
            "device": self.device,
            "is_half": self.is_half,
            "filter_radius": self.filter_radius,
            "resample_sr": self.resample_sr,
            "rms_mix_rate": self.rms_mix_rate,
            "protect": self.protect,
        }
        files = {
            "input_file": audio_bytes,
        }

        response = requests.post(self.api, params=data, files=files)
        return response.content


__all__ = [
    "RVC"
]
