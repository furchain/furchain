from urllib.parse import urljoin

import requests

from furchain.audio.schema import TTS
from furchain.config import AudioConfig


class ChatTTS(TTS):
    def __init__(self, api_base: str = None, voice: str = None, speed: int = 5,
                 temperature: float = 0.3, top_p: float = 0.7, top_k: int = 20, skip_refine: bool = False,
                 text_seed: int = 42, refine_max_new_token: int = 384, infer_max_new_token: int = 2048):
        api_base = api_base or AudioConfig.get_chat_tts_api_base()
        self.api = urljoin(api_base, "tts")
        self.payload = {
            'voice': voice,
            'speed': speed,
            'temperature': temperature,
            'top_p': top_p,
            'top_k': top_k,
            'skip_refine': int(skip_refine),
            'text_seed': text_seed,
            'refine_max_new_token': refine_max_new_token,
            'infer_max_new_token': infer_max_new_token,
            'wav': 1
        }

    def run(self, text: str, **kwargs) -> bytes:
        payload = self.payload.copy()
        payload['text'] = text
        payload.update(kwargs)
        return requests.post(self.api, data=payload).content
