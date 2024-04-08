from furchain.audio.speech.gpt_sovits import GPTSovitsClient
from furchain.audio.schema import VC
from furchain.config import AudioConfig


class GPTSovitsVC(VC):

    def __init__(self, api_base: str = None, refer_wav_path: str = None, prompt_text: str = None,
                 prompt_language: str = None):
        super().__init__()
        if api_base is None:
            api_base = AudioConfig.get_gpt_sovits_api_base()
        self.client = GPTSovitsClient(api_base, refer_wav_path, prompt_text, prompt_language)

    def run(self, audio_bytes: bytes, noise_scale:float = 0.5) -> bytes:
        return self.client.vc(audio_bytes, noise_scale)
