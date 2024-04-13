from furchain.audio.schema import VC
from furchain.audio.speech.gpt_sovits import GPTSovitsClient
from furchain.config import AudioConfig


class GPTSovitsVC(VC):

    def __init__(self, prompt_wav: bytes, api_base: str = None,
                 prompt_language: str = 'auto'):
        "refer_wav:bytes, prompt_wav: bytes, prompt_text:str, "
        super().__init__()
        if api_base is None:
            api_base = AudioConfig.get_gpt_sovits_api_base()
        self.prompt_wav = prompt_wav
        self.client = GPTSovitsClient(api_base, None, None, prompt_language)

    def run(self, audio_bytes: bytes, prompt_text: str, noise_scale: float = 0.5) -> bytes:
        return self.client.vc(audio_bytes, self.prompt_wav, prompt_text, noise_scale)
