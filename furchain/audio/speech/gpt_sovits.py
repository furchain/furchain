from typing import Optional

import requests
from langchain_core.runnables import RunnableConfig

from furchain.audio.schema import TTS
from furchain.config import AudioConfig


class GPTSovitsClient:
    def __init__(self, api_base: str, refer_wav_path: str = None, prompt_text: str = None, prompt_language: str = None):
        self.api_base = api_base
        self.refer_wav_path = refer_wav_path
        self.prompt_text = prompt_text
        self.prompt_language = prompt_language

    def change_refer(self, refer_wav_path: str, prompt_text: str):
        self.refer_wav_path = refer_wav_path
        self.prompt_text = prompt_text

    def infer(self, text: str, text_language: str):
        payload = {
            'text': text,
            'text_language': text_language,
            'prompt_text': self.prompt_text,
            'prompt_language': self.prompt_language,
            'refer_wav_path': self.refer_wav_path
        }
        response = requests.post(self.api_base, json=payload)
        return response.content


class GPTSovits(TTS):

    def __init__(self, api_base: str = None, refer_wav_path: str = None, prompt_text: str = None,
                 prompt_language: str = None):
        super().__init__()
        if api_base is None:
            api_base = AudioConfig.get_gpt_sovits_api_base()
        self.client = GPTSovitsClient(api_base, refer_wav_path, prompt_text, prompt_language)

    def run(self, text: str, text_language: str) -> bytes:
        return self.client.infer(text, text_language)

    def invoke(
            self, input: dict, config: Optional[RunnableConfig] = None
    ) -> bytes:
        return self.run(**input)
