import abc
from typing import Optional, Any, Iterator, Iterable

from langchain_core.runnables import RunnableConfig, Runnable
from langchain_core.runnables.utils import Output

from furchain.utils.broadcaster import iterator_callback_broadcaster


class TTS(Runnable, metaclass=abc.ABCMeta):
    """
    The TTS class is an abstract base class that represents a Text-to-Speech (TTS) service.
    It inherits from the Runnable class and uses the ABCMeta metaclass to enforce the implementation
    of the abstract methods in any concrete subclass.
    """

    def run(self, text: str, *args, **kwargs):
        raise NotImplementedError

    def invoke(self, input: dict | str, config: Optional[RunnableConfig] = None) -> Output:
        if isinstance(input, str):
            input = {"text": input}
        return self.run(**input)


class VC(Runnable, metaclass=abc.ABCMeta):
    """
    The VC class is an abstract base class that represents a Voice Conversion (VC) service.
    It inherits from the Runnable class and uses the ABCMeta metaclass to enforce the implementation
    of the abstract methods in any concrete subclass.

    Methods:
        run(audio_bytes: bytes) -> bytes: An abstract method that must be implemented by any concrete subclass.
            It should take audio bytes and convert it, returning the resulting audio as bytes.
        invoke(input: dict | bytes, config: Optional[RunnableConfig] = None) -> bytes:
            Invokes the VC service with the provided input and configuration.
            The input can be either bytes or a dictionary. If it's bytes, it's converted into a dictionary
            with the key 'audio_bytes'. The resulting audio is returned as bytes.
        stream(input: Iterable[bytes], config: Optional[RunnableConfig] = None, **kwargs: Optional[Any]) -> Iterator[Output]:
            Streams the input bytes through the VC service, returning an iterator of Output objects.
    """

    @abc.abstractmethod
    def run(self, audio_bytes: bytes) -> bytes:
        """
        An abstract method that must be implemented by any concrete subclass.
        It should take audio bytes and convert it, returning the resulting audio as bytes.
        """
        raise NotImplementedError

    def invoke(
            self, input: dict | bytes, config: Optional[RunnableConfig] = None
    ) -> bytes:
        """
        Invokes the VC service with the provided input and configuration.
        The input can be either bytes or a dictionary. If it's bytes, it's converted into a dictionary
        with the key 'audio_bytes'. The resulting audio is returned as bytes.
        """
        if isinstance(input, bytes):
            input = {'audio_bytes': input}
        return self.run(**input)

    def stream(
            self,
            input: Iterable[bytes],
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        """
        Streams the input bytes through the VC service, returning an iterator of Output objects.
        """

        def _run(audio_bytes):
            return self.run(audio_bytes=audio_bytes)

        audio_bytes_queue, = iterator_callback_broadcaster(input, callbacks=[_run])
        for i in audio_bytes_queue:
            yield i


class STT(Runnable, metaclass=abc.ABCMeta):
    """
    The STT class is an abstract base class that represents a Speech-to-Text (STT) service.
    It inherits from the Runnable class and uses the ABCMeta metaclass to enforce the implementation
    of the abstract methods in any concrete subclass.
    """
    ...


class FeatureExtraction(Runnable, metaclass=abc.ABCMeta):
    """
    The FeatureExtraction class is an abstract base class that represents a feature extraction service.
    It inherits from the Runnable class and uses the ABCMeta metaclass to enforce the implementation
    of the abstract methods in any concrete subclass.
    """
    ...