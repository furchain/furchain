import json
from typing import List

import requests

from furchain.config import TextConfig


class LlamaCppClient:
    """
    A client for interacting with the Llama C++ API.

    Attributes:
        base_url (str): The base URL for the Llama C++ API.
        headers (dict): The headers to use for the API requests.

    Methods:
        health: Returns the health status of the Llama C++ API.
        props: Returns the properties of the Llama C++ API.
        stream(data: dict, **kwargs): Streams data to the Llama C++ API.
        complete(data: dict, **kwargs): Sends a completion request to the Llama C++ API.
        tokenize(content: str) -> List[int]: Tokenizes a string.
        detokenize(tokens: List[int]): Detokenizes a list of tokens.
        embedding(content: str): Returns the embedding of a string.
    """

    def __init__(self, base_url=None, api_key=None):
        """
        Initializes the LlamaCppClient.

        Args:
            base_url (str, optional): The base URL for the Llama C++ API. Defaults to None.
            api_key (str, optional): The API key for the Llama C++ API. Defaults to None.
        """
        if base_url is None:
            base_url = TextConfig.get_llama_cpp_api_base()
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}' if api_key else ''
        }

    @property
    def health(self):
        """
        Returns the health status of the Llama C++ API.

        Returns:
            dict: The health status.
        """
        response = requests.get(f"{self.base_url}/health", headers=self.headers)
        return response.json()

    @property
    def props(self):
        """
        Returns the properties of the Llama C++ API.

        Returns:
            dict: The properties.
        """
        response = requests.get(f"{self.base_url}/props", headers=self.headers)
        return response.json()

    def stream(self, data: dict, **kwargs):
        """
        Streams data to the Llama C++ API.

        Args:
            data (dict): The data to stream.
            **kwargs: Additional keyword arguments.

        Yields:
            dict: The response from the API.
        """
        data.update(kwargs)
        data["stream"] = True
        response = requests.post(f"{self.base_url}/completion", headers=self.headers, json=data, stream=True)
        for i in response.iter_lines():
            if i:
                yield json.loads(i.decode('utf-8').removeprefix('data: '))

    def complete(self, data: dict, **kwargs):
        """
        Sends a completion request to the Llama C++ API.

        Args:
            data (dict): The data for the completion request.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The response from the API.
        """
        data.update(kwargs)
        response = requests.post(f"{self.base_url}/completion", headers=self.headers, json=data)
        return response.json()

    def tokenize(self, content: str) -> List[int]:
        """
        Tokenizes a string.

        Args:
            content (str): The string to tokenize.

        Returns:
            List[int]: The tokens.
        """
        data = {'content': content}
        response = requests.post(f"{self.base_url}/tokenize", headers=self.headers, json=data)
        return response.json()['tokens']

    def detokenize(self, tokens: List[int]):
        """
        Detokenizes a list of tokens.

        Args:
            tokens (List[int]): The tokens to detokenize.

        Returns:
            str: The detokenized string.
        """
        data = {'tokens': tokens}
        response = requests.post(f"{self.base_url}/detokenize", headers=self.headers, json=data)
        return response.json()['content']

    def embedding(self, content: str):
        """
        Returns the embedding of a string.

        Args:
            content (str): The string to get the embedding of.

        Returns:
            list: The embedding.
        """
        data = {"content": content}
        response = requests.post(f"{self.base_url}/embedding", headers=self.headers, json=data)
        return response.json()['embedding']


__all__ = [
    "LlamaCppClient"
]
