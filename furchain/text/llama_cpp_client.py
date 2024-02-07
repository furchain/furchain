import json
from typing import List

import requests

from furchain.config import TextConfig


class LlamaCppClient:
    """
      https://github.com/ggerganov/llama.cpp/tree/master/examples/server
      """

    def __init__(self, base_url=None, api_key=None):
        if base_url is None:
            base_url = TextConfig.get_llama_cpp_api_base()
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}' if api_key else ''
        }

    @property
    def health(self):
        response = requests.get(f"{self.base_url}/health", headers=self.headers)
        return response.json()

    @property
    def props(self):
        response = requests.get(f"{self.base_url}/props", headers=self.headers)
        return response.json()

    def stream(self, data: dict, **kwargs):
        data.update(kwargs)
        data["stream"] = True
        response = requests.post(f"{self.base_url}/completion", headers=self.headers, json=data, stream=True)
        for i in response.iter_lines():
            if i:
                yield json.loads(i.decode('utf-8').removeprefix('data: '))

    def complete(self, data: dict, **kwargs):
        data.update(kwargs)
        response = requests.post(f"{self.base_url}/completion", headers=self.headers, json=data)
        return response.json()

    def tokenize(self, content: str) -> List[int]:
        data = {'content': content}
        response = requests.post(f"{self.base_url}/tokenize", headers=self.headers, json=data)
        return response.json()['tokens']

    def detokenize(self, tokens: List[int]):
        data = {'tokens': tokens}
        response = requests.post(f"{self.base_url}/detokenize", headers=self.headers, json=data)
        return response.json()['content']

    def embedding(self, content: str):
        data = {"content": content}
        response = requests.post(f"{self.base_url}/embedding", headers=self.headers, json=data)
        return response.json()['embedding']
