import requests

from furchain.audio.schema import VC
from furchain.config import AudioConfig


class RVC(VC):
    """
    This class is a subclass of VC and represents the Retrieval-based Voice Conversion (RVC) model.
    It is used to convert the voice of a speaker to another speaker's voice.
    The conversion is done by sending a POST request to the RVC API with the necessary parameters and the audio file.

    Attributes:
        speaker (str): The speaker whose voice is to be converted.
        api (str): The URL of the RVC API. If not provided, it is fetched from the AudioConfig.
        index_path (str): The path to the index file.
        f0up_key (int): The key for the fundamental frequency (F0) upscaling. Default is 0.
        f0method (str): The method for F0 extraction. Default is "rmvpe".
        index_rate (float): The rate for the index. Default is 0.66.
        device (str): The device to be used for the conversion.
        is_half (bool): Whether to use half precision or not. Default is False.
        filter_radius (int): The radius of the filter. Default is 3.
        resample_sr (int): The sample rate for resampling. Default is 0.
        rms_mix_rate (float): The rate for the RMS mix. Default is 1.
        protect (float): The protection rate. Default is 0.33.
    """

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

    def run(self, audio_bytes: bytes, **kwargs) -> bytes:
        """
        This method sends a POST request to the RVC API with the necessary parameters and the audio file.
        It then returns the response content which is the converted audio.

        Args:
            audio_bytes (bytes): The audio file in bytes.

        Returns:
            bytes: The converted audio in bytes.
        """
        data = {
            "model_name": self.speaker,
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
        data.update(kwargs)
        files = {
            "input_file": audio_bytes,
        }

        response = requests.post(self.api, params=data, files=files)
        return response.content


__all__ = [
    "RVC"
]
