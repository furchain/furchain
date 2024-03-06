from typing import Optional

import requests
from langchain_core.runnables import RunnableConfig

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

    def __init__(self, api_base: str, refer_wav_path: str = None, prompt_text: str = None, prompt_language: str = None):
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


class GPTSovits(TTS):
    """
    This class is a subclass of TTS and represents the GPT-Sovits Text-to-Speech (TTS) model.
    It is used to convert text to speech.

    Attributes:
        client (GPTSovitsClient): The client for the GPT-Sovits API.
    """

    def __init__(self, api_base: str = None, refer_wav_path: str = None, prompt_text: str = None,
                 prompt_language: str = None):
        super().__init__()
        if api_base is None:
            api_base = AudioConfig.get_gpt_sovits_api_base()
        self.client = GPTSovitsClient(api_base, refer_wav_path, prompt_text, prompt_language)

    def run(self, text: str, text_language: str) -> bytes:
        """
        This method converts the given text to speech by calling the infer method of the client.

        Args:
            text (str): The text to be converted to speech.
            text_language (str): The language of the text.

        Returns:
            bytes: The speech in bytes.
        """
        return self.client.infer(text, text_language)

    def invoke(
            self, input: dict, config: Optional[RunnableConfig] = None
    ) -> bytes:
        """
        This method is a wrapper for the run method. It takes a dictionary as input and unpacks it to call the run method.

        Args:
            input (dict): The input parameters for the run method.
            config (Optional[RunnableConfig]): The configuration for the runnable. Default is None.

        Returns:
            bytes: The speech in bytes.
        """
        return self.run(**input)


__all__ = [
    "GPTSovits"
]
