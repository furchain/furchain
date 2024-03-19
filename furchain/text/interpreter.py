"""Interprete LLM output into actions
let all llm output pass in this
for string, print
for speaking, audio
for image, display

Two timeline:
1. token sequence
2. action sequence"""

# LLM Token --interpreter--> ActionToken
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Optional, Any, Iterator

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Output, Input

from furchain.audio.schema import TTS
from furchain.audio.utils import play_audio_bytes
from furchain.text.tools import ToolSymbol, ToolCall

EXECUTOR = ThreadPoolExecutor(max_workers=4)


class ActionToken:
    def __init__(self, task: list[Future] | Future = None, callback: list[Callable] | Callable = lambda x: None):
        self.task = task if isinstance(task, list) else [task]
        self.callback = callback if isinstance(callback, list) else [callback]

    def __add__(self, other):
        if isinstance(other, ActionToken):
            return ActionToken(self.task + other.task, self.callback + other.callback)
        else:
            raise TypeError("Unsupported operand type for +: 'ActionToken' and '{}'".format(type(other).__name__))

    def eval(self):
        for task, callback in zip(self.task, self.callback):
            if task is None:
                continue
            callback(task.result())


class Tokenizer:

    def check_active(self, current_token: str, history_tokens: str) -> bool:
        raise NotImplementedError

    def encode(self, current_token: str, history_tokens: str) -> None | ActionToken:
        raise NotImplementedError


class TTSTokenizer(Tokenizer):

    def __init__(self, tts: TTS, speaker: str, evaluate_func: Callable = play_audio_bytes):
        self.tts = tts
        self.speaker = speaker
        self.evaluate_func = evaluate_func
        self._active = False

    def check_active(self, current_token: str, history_tokens: str) -> bool:
        return self._active or history_tokens.startswith(self.speaker + ':')

    def encode(self, current_token: str, history_tokens: str) -> None | ActionToken:
        if current_token == '':
            result = ActionToken(EXECUTOR.submit(self.tts.invoke, history_tokens), self.evaluate_func)
            print(history_tokens)
            return result
            return None


class ToolTokenizer(Tokenizer):

    def submit(self, token: str) -> None | Output:
        if ToolSymbol.TOOL_NAME.value in token:
            self.activate()
        if self.is_active:
            self.buffer += token
            if ToolSymbol.TOOL_END.value in token:
                self.deactivate()
        tool_calls = ToolCall.from_string(self.buffer)
        for tool_call in tool_calls:
            tool_call.tool.invoke(tool_call.tool_parameter)
            return self.tokenizer.invoke(self.buffer)
        self.buffer += token
        return None


class Interpreter(Runnable):
    """
    None: no action
    Callable: take instant action
    Future: submit to executor
    """

    def __init__(self, tokenizers: list[Tokenizer]):
        self.tokenizers = tokenizers
        self.history_tokens = ''

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        result = ActionToken()
        for action_token in self.stream(input):
            result += action_token
        return result

    def stream(
            self,
            input: Input,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        current_active_tokenizer = None
        for current_token in input:
            for tokenizer in self.tokenizers:
                is_active = tokenizer.check_active(current_token, self.history_tokens)
                if is_active:
                    if tokenizer != current_active_tokenizer and current_active_tokenizer is not None:
                        action = current_active_tokenizer.encode('', self.history_tokens)
                        if action is not None:
                            yield action
                    current_active_tokenizer = tokenizer
                    action = tokenizer.encode(current_token, self.history_tokens)
                    print(action)
                    if action is not None:
                        yield action
                    continue
            self.history_tokens += current_token
