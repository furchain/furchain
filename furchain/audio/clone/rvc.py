import requests

from furchain.audio.schema import ParrotVC
from furchain.config import AudioConfig


class RVC(ParrotVC):
    """https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/pull/1614"""
    
    default_speaker = "klee-jp"

    def __init__(self, api: str = None, **kwargs):
        super().__init__(**kwargs)
        if api is None:
            api = AudioConfig.get_rvc_api()
        self.api = api

    def run(self, audio_bytes: bytes, speaker: str = "klee-jp", index_path: str = None, f0up_key: int = 0,
            f0method: str = "rmvpe", index_rate: float = 0.66, device: str = None,
            is_half: bool = False, filter_radius: int = 3, resample_sr: int = 0,
            rms_mix_rate: float = 1, protect: float = 0.33, response_format='wav') -> bytes:
        data = {
            "model_name": speaker,
            "index_path": index_path,
            "f0up_key": f0up_key,
            "f0method": f0method,
            "index_rate": index_rate,
            "device": device,
            "is_half": is_half,
            "filter_radius": filter_radius,
            "resample_sr": resample_sr,
            "rms_mix_rate": rms_mix_rate,
            "protect": protect,
            "response_format": response_format,
        }
        files = {
            "input_file": audio_bytes,
        }

        response = requests.post(self.api, params=data, files=files)
        return response.content


__all__ = [
    "RVC"
]
