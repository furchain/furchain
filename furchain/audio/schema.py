import abc
from typing import Optional, Any

from langchain_core.runnables import RunnableConfig, Runnable

from furchain.logger import logger


class ParrotTTS(Runnable, metaclass=abc.ABCMeta):

    def __init__(self, **kwargs):
        super().__init__()
        self._default_kwargs = kwargs

    @classmethod
    @abc.abstractmethod
    def run(cls, text: str, *args, **kwargs) -> bytes:
        raise NotImplementedError

    def invoke(
            self, input: dict | str, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> bytes:
        params = {**self._default_kwargs}
        params.update(kwargs)
        logger.debug(f"{params=}")
        if isinstance(input, str):
            input = {'text': input}
        return self.run(**{**params, **input})


class ParrotVC(Runnable, metaclass=abc.ABCMeta):

    def __init__(self, **kwargs):
        super().__init__()
        self._default_kwargs = kwargs

    @classmethod
    @abc.abstractmethod
    def run(cls, audio_bytes: bytes, *args, **kwargs) -> bytes:
        raise NotImplementedError

    def invoke(
            self, input: dict | bytes, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> bytes:
        params = {**self._default_kwargs}
        params.update(kwargs)
        logger.debug(f"{params=}")
        if isinstance(input, bytes):
            input = {'audio_bytes': input}
        return self.run(**params, **input)


class ParrotSTT(Runnable, metaclass=abc.ABCMeta):
    def __init__(self, **kwargs):
        super().__init__()
        self._default_kwargs = kwargs
