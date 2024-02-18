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

from furchain.audio.schema import ParrotSTT
from furchain.audio.utils.get_format import get_format_from_magic_bytes
from furchain.config import AudioConfig
from furchain.logger import logger
from furchain.utils.iterator import BufferIterator

END_MESSAGE = json.dumps({"is_speaking": False})

class FunASRSession:
    """
    Deployment: https://github.com/alibaba-damo-academy/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online.md
    Protocol: https://github.com/alibaba-damo-academy/FunASR/blob/main/runtime/docs/websocket_protocol.md
    """

    def __init__(self,
                 api: str = "ws://localhost:10096",
                 mode: Literal["online", "offline", '2pass'] = "offline", format: Literal["pcm", "mp3", "mp4"] = "pcm",
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
        if self.api.startswith('wss'):
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context = None
        self.websocket = await websockets.connect(self.api, subprotocols=[websockets.Subprotocol("binary")],
                                                  ping_interval=None, ssl=ssl_context)

    async def astream_audio(self, audio_stream: Iterable, handler: Callable):
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
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        if self.api.startswith('wss'):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context = None
        self.websocket = websocket.create_connection(self.api,
                                                     sslopt={"cert_reqs": ssl.CERT_NONE} if ssl_context else {})

    def stream_audio(self, audio_stream, handler):
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
        if self.websocket is not None:
            self.websocket.close()
            self.websocket = None


class FunASR(ParrotSTT):

    def __init__(self, api: str = None, **kwargs):
        if api is None:
            api = AudioConfig.get_funasr_api()
        kwargs["api"] = api
        super().__init__(**kwargs)
        self._default_kwargs = kwargs

    def invoke(self, input: Input, **kwargs) -> Output:
        if not isinstance(input, bytes):
            input = b''.join(input)
        result = ''
        for i in self.stream(input, **kwargs):
            result += i['text']
        i['text'] = result
        if result == '':
            if audio_format := get_format_from_magic_bytes(input) != 'unknown':
                warnings.warn(
                    f"You need to convert `{audio_format}` into PCM format with `furchain.audio.utils.convert.convert_to_pcm`.")
        return i

    def stream(
            self,
            input: Iterable,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
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

        session = FunASRSession(**self._default_kwargs, **kwargs)

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
