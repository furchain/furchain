import asyncio
import json
import ssl
import threading
import uuid
from typing import Literal, Awaitable, Iterable

import websocket
import websockets

from furchain.logger import logger

END_MESSAGE = json.dumps({"is_speaking": False})


class FunASRSession:
    """
    Deployment: https://github.com/alibaba-damo-academy/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online.md
    Protocol: https://github.com/alibaba-damo-academy/FunASR/blob/main/runtime/docs/websocket_protocol.md
    """

    def __init__(self,
                 host="localhost", port=10096, ssl_enabled=False,
                 mode: Literal["online", "offline", '2pass'] = "offline", format: Literal["pcm", "mp3", "mp4"] = "pcm",
                 wav_name: str = None,
                 itn: bool = True,
                 sr: int = 16000, hotwords: dict = None, **kwargs):

        self.host = host
        self.port = port
        self.ssl_enabled = ssl_enabled
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
        if self.ssl_enabled:
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = f"wss://{self.host}:{self.port}"
        else:
            uri = f"ws://{self.host}:{self.port}"
            ssl_context = None
        self.websocket = await websockets.connect(uri, subprotocols=[websockets.Subprotocol("binary")],
                                                  ping_interval=None, ssl=ssl_context)

    async def astream_audio(self, audio_stream: Iterable, handler: Awaitable):
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
            # When done sending, cancel the receive task
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            logger.exception(e)
        finally:
            await self.websocket.send(END_MESSAGE)
            await receive_task

    async def areceive_messages(self, handler):
        try:
            while True:
                data = await self.websocket.recv()
                message = json.loads(data)
                await handler(message)
                if message.get('is_final'):
                    break
        except websockets.exceptions.ConnectionClosed:
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
        if self.ssl_enabled:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = f"wss://{self.host}:{self.port}"
        else:
            uri = f"ws://{self.host}:{self.port}"
            ssl_context = None
        self.websocket = websocket.create_connection(uri, sslopt={"cert_reqs": ssl.CERT_NONE} if ssl_context else {})

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
                    message = json.loads(data)
                    handler(data)
                    if message.get('is_final'):
                        break
            except websocket.WebSocketConnectionClosedException:
                pass

        # Start receiving messages in a separate thread
        receive_thread = threading.Thread(target=receive_messages, args=(handler,))
        receive_thread.start()

        try:
            for chunk in audio_stream:
                self.websocket.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                # No sleep needed here, as this is a synchronous/blocking call

        except Exception as e:
            logger.exception(e)
        finally:
            self.websocket.send(END_MESSAGE)
            receive_thread.join()

    def close(self):
        if self.websocket is not None:
            self.websocket.close()
            self.websocket = None
