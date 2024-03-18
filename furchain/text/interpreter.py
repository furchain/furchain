"""Interprete LLM output into actions
let all llm output pass in this
for string, print
for speaking, audio
for image, display

Two timeline:
1. token sequence
2. action sequence"""
import enum
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Optional

from langchain_core.output_parsers.base import T
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Output

from furchain.text.tools import ToolSymbol, ToolCall

EXECUTOR = ThreadPoolExecutor(max_workers=4)


class SentenceTokenizer:
    def __init__(self, tokenizer: Runnable):
        self._active = True
        self.buffer = ''
        self.tokenizer = tokenizer

    def activate(self) -> None:
        self._active = True

    def deactivate(self) -> None:
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def encode(self, token: str) -> None | Future:
        if self.is_active:
            if len(self.buffer) < 10:
                self.buffer += token
                return None
            return EXECUTOR.submit(self.tokenizer.invoke, self.buffer)


class ToolTokenizer(SentenceTokenizer):

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


class Interpreter:
    """
    None: no action
    Callable: take instant action
    Future: submit to executor
    """

    def __init__(self, num_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=num_workers)

    class State(enum.Enum):
        """State of the interpreter."""
        TOOL = enum.auto()
        PARSING = enum.auto()
        EXECUTING = enum.auto()
        DONE = enum.auto()

    def _diff(self, prev: Optional[T], next: T) -> T:
        if prev is None:
            return next
        return next

    def parse(self, text: str) -> T:
        return text

    task: Future
    result = task.result()
    if isinstance(result, Callable):
        result = result()
