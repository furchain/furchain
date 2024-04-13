import asyncio
import json
import ssl
import threading
import uuid
import warnings
from typing import Literal, Iterable, Optional, Any, Iterator, Callable

import websocket
import websockets
from langchain_core.runnables.utils import Output, Input

from furchain.audio.schema import STT
from furchain.audio.utils.get_format import get_format_from_magic_bytes
from furchain.config import AudioConfig
from furchain.logger import logger
from furchain.utils.iterator import BufferIterator

END_MESSAGE = json.dumps({"is_speaking": False})


class FunASRSession:
    """
    This class represents a session with the FunASR API.
    It is used to send and receive messages to and from the API.

    Attributes:
        api (str): The URL of the FunASR API.
        websocket (websocket.WebSocket): The WebSocket used to communicate with the API.
        config (dict): The configuration for the session.
    """

    def __init__(self,
                 api: str = "ws://localhost:10096",
                 mode: Literal["online", "offline", '2pass'] = "offline",
                 format: Literal["pcm", "mp3", "mp4", "wav"] = "pcm",
                 wav_name: str = None,
                 itn: bool = True,
                 sr: int = 16000, hotwords: dict = None, **kwargs):

        self.api = api
        self.websocket = None
        self.config = {
            "mode": mode,
            "wav_format": format,  # realtime transcription only supports 'pcm'
            "audio_fs": sr,
            "itn": itn,
            "wav_name": wav_name if wav_name else str(uuid.uuid4()),
            "is_speaking": True,
            "chunk_size": [5, 10, 5],
            **kwargs
        }
        if hotwords:
            self.config.update({'hotwords': json.dumps(hotwords)})

    async def __aenter__(self):
        await self.aconnect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def aconnect(self):
        """
        This method connects to the FunASR API using a WebSocket.
        """
        if self.api.startswith('wss'):
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context = None
        self.websocket = await websockets.connect(self.api, subprotocols=[websockets.Subprotocol("binary")],
                                                  ping_interval=None, ssl=ssl_context)

    async def astream_audio(self, audio_stream: Iterable, handler: Callable):
        """
        This method sends the audio stream to the FunASR API and starts receiving messages.

        Args:
            audio_stream (Iterable): The audio stream to be sent.
            handler (Callable): The function to handle the received messages.
        """
        if self.websocket is None:
            raise RuntimeError("Session is not connected")

        await self.websocket.send(json.dumps(self.config))

        # Start receiving messages in a separate task
        receive_task = asyncio.create_task(self.areceive_messages(handler))

        try:
            for chunk in audio_stream:
                await self.websocket.send(chunk)
                await asyncio.sleep(0.005)
        except Exception as e:
            logger.exception(e)
            raise e
        finally:
            try:
                await self.websocket.send(END_MESSAGE)
            except websockets.exceptions.ConnectionClosed:
                pass
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass

    async def areceive_messages(self, handler):
        """
        This method receives messages from the FunASR API and passes them to the handler.

        Args:
            handler (Callable): The function to handle the received messages.
        """
        try:
            while True:
                data = await self.websocket.recv()
                message = json.loads(data)
                await handler(message)
                if message.get('is_final'):
                    break
        except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError):
            pass

    async def aclose(self):
        """
        This method closes the connection to the FunASR API.
        """
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """
        This method connects to the FunASR API using a WebSocket.
        """
        if self.api.startswith('wss'):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context = None
        self.websocket = websocket.create_connection(self.api,
                                                     sslopt={"cert_reqs": ssl.CERT_NONE} if ssl_context else {})

    def stream_audio(self, audio_stream, handler):
        """
        This method sends the audio stream to the FunASR API and starts receiving messages.

        Args:
            audio_stream (Iterable): The audio stream to be sent.
            handler (Callable): The function to handle the received messages.
        """
        if self.websocket is None:
            raise RuntimeError("Session is not connected")
        message = json.dumps(self.config)
        self.websocket.send(message)

        # Function to run in a separate thread
        def receive_messages(handler):
            try:
                while True:
                    data = self.websocket.recv()
                    try:
                        message = json.loads(data)
                        handler(message)
                    except Exception as e:
                        logger.exception(e)
                        try:
                            self.websocket.send(END_MESSAGE)
                        except (websocket.WebSocketConnectionClosedException, AttributeError):
                            pass
                        self.close()
                        return
                    if message.get('is_final'):
                        break
            except (websocket.WebSocketConnectionClosedException, AttributeError):
                pass

        # Start receiving messages in a separate thread
        receive_thread = threading.Thread(target=receive_messages, args=(handler,))
        receive_thread.start()

        try:
            for chunk in audio_stream:
                self.websocket.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                # No sleep needed here, as this is a synchronous/blocking call
        except (AttributeError,
                websocket.WebSocketConnectionClosedException):  # websocket is None (closed), no need to raise exception
            pass

        except Exception as e:
            self.close()
            logger.exception(e)
            # handler(e)
            raise e
        finally:
            try:
                self.websocket.send(END_MESSAGE)
            except (websocket.WebSocketConnectionClosedException, AttributeError):
                pass
            receive_thread.join()

    def close(self):
        """
        This method closes the connection to the FunASR API.
        """
        if self.websocket is not None:
            self.websocket.close()
            self.websocket = None


class FunASR(STT):
    """
    This class is a subclass of STT and represents the FunASR Speech-to-Text (STT) model.
    It is used to convert speech to text.

    Attributes:
        session (FunASRSession): The session with the FunASR API.
    """

    def __init__(self, api: str = None, mode: Literal["online", "offline", '2pass'] = "offline",
                 format: Literal["pcm", "mp3", "mp4"] = "pcm", **kwargs):
        if api is None:
            api = AudioConfig.get_funasr_api()
        self.session = FunASRSession(api=api, mode=mode, format=format, **kwargs)

    def invoke(self, input: Input, **kwargs) -> Output:
        """
        This method converts the given input to text.

        Args:
            input (Input): The input to be converted to text.
            **kwargs: Additional keyword arguments.

        Returns:
            Output: The text.
        """
        if not isinstance(input, bytes):
            input = b''.join(input)
        result = ''
        kwargs['mode'] = 'offline'
        i = None
        for i in self.stream(input, **kwargs):
            result += i['text']
        if i is None:
            raise RuntimeError("FunASR failed to return a valid result.")
        if result == '':
            if audio_format := get_format_from_magic_bytes(input):
                warnings.warn(
                    f"You need to convert `{audio_format}` into PCM format with `furchain.audio.utils.convert.convert_to_pcm`.")

        i['text'] = result
        return i

    def stream(
            self,
            input: Iterable,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        """
        This method converts the given input to text in a streaming manner.

        Args:
            input (Iterable): The input to be converted to text.
            **kwargs: Additional keyword arguments.

        Returns:
            Iterator[Output]: The text.
        """
        if isinstance(input, bytes):
            def _input(x):
                yield x

            input = _input(input)

        iterator = BufferIterator()

        def _response_handler(message):
            try:
                iterator.put(message)
                if message.get('is_final'):
                    iterator.terminate()
            except Exception:
                iterator.terminate()

        session = self.session

        def _stream():
            try:
                session.stream_audio(input, _response_handler)
            except Exception as e:
                iterator.terminate()
                raise e

        stream_thread = threading.Thread(target=_stream)

        try:
            session.connect()
            stream_thread.start()
            yield from iterator
        finally:
            session.close()
            if stream_thread.is_alive():
                stream_thread.join()


__all__ = [
    "FunASR"
]
