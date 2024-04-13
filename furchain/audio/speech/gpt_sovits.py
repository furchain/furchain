from urllib.parse import urljoin

import requests

from furchain.audio.schema import TTS
from furchain.config import AudioConfig


class GPTSovitsClient:
    """
    This class represents the client for the GPT-Sovits API.
    It is used to send POST requests to the API with the necessary parameters and receive the response.

    Attributes:
        api_base (str): The base URL of the GPT-Sovits API.
        refer_wav_path (str): The path to the reference WAV file.
        prompt_text (str): The prompt text.
        prompt_language (str): The language of the prompt text.
    """

    def __init__(self, api_base: str, refer_wav_path: str = None, prompt_text: str = None, prompt_language: str = 'auto'):
        self.api_base = api_base
        self.refer_wav_path = refer_wav_path
        self.prompt_text = prompt_text
        self.prompt_language = prompt_language

    def change_refer(self, refer_wav_path: str, prompt_text: str):
        """
        This method changes the reference WAV file and the prompt text.

        Args:
            refer_wav_path (str): The new path to the reference WAV file.
            prompt_text (str): The new prompt text.
        """
        self.refer_wav_path = refer_wav_path
        self.prompt_text = prompt_text

    def infer(self, text: str, text_language: str):
        """
        This method sends a POST request to the GPT-Sovits API with the necessary parameters and returns the response content.

        Args:
            text (str): The text to be converted to speech.
            text_language (str): The language of the text.

        Returns:
            bytes: The speech in bytes.
        """
        payload = {
            'text': text,
            'text_language': text_language,
            'prompt_text': self.prompt_text,
            'prompt_language': self.prompt_language,
            'refer_wav_path': self.refer_wav_path
        }
        response = requests.post(self.api_base, json=payload)
        return response.content

    def vc(self, refer_wav:bytes, prompt_wav: bytes, prompt_text:str, noise_scale: float = 0.5):
        params = {
            'noise_scale': noise_scale,
            'prompt_text': prompt_text,
            'prompt_language': self.prompt_language,

        }
        file = {
            'prompt_wav': prompt_wav,
            'refer_wav': refer_wav
        }
        response = requests.post(urljoin(self.api_base, "vc"), params=params, files=file)
        return response.content



class GPTSovits(TTS):
    """
    This class is a subclass of TTS and represents the GPT-Sovits Text-to-Speech (TTS) model.
    It is used to convert text to speech.

    Attributes:
        client (GPTSovitsClient): The client for the GPT-Sovits API.
    """

    def __init__(self, api_base: str = None, refer_wav_path: str = None, prompt_text: str = None,
                 prompt_language: str = None, text_language=None):
        super().__init__()
        if api_base is None:
            api_base = AudioConfig.get_gpt_sovits_api_base()
        self.text_language = text_language
        self.client = GPTSovitsClient(api_base, refer_wav_path, prompt_text, prompt_language)

    def run(self, text: str, text_language: str = None) -> bytes:
        """
        This method converts the given text to speech by calling the infer method of the client.

        Args:
            text (str): The text to be converted to speech.
            text_language (str): The language of the text.

        Returns:
            bytes: The speech in bytes.
        """
        if text_language is None:
            text_language = self.text_language
        return self.client.infer(text, text_language)




__all__ = [
    "GPTSovits"
]
