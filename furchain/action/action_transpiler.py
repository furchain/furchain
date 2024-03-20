"""Interprete LLM output into actions
let all llm output pass in this
for string, print
for speaking, audio
for image, display

Two timeline:
1. token sequence
2. action sequence"""
import enum
# LLM Token --interpreter--> ActionToken
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Any, Iterator, Callable

import emoji
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Output, Input

EXECUTOR = ThreadPoolExecutor(max_workers=4)


class ActionType(enum.Enum):
    SPEAK = '🗣️'
    DISPLAY = '🖼'
    SING = '🎤'
    TOOL = '🔨'
    END = '🔚'

    @classmethod
    def from_emoji(cls, emoji: str):
        for action_type in cls:
            if action_type.value == emoji:
                return action_type
        raise ValueError(f'No ActionType found for emoji: {emoji}')


class ActionParameter(enum.Enum):
    SPEAKER = '👤'
    TEXT = '📄'
    IMAGE = '🖼'
    AUDIO = '🎤'
    TOOL_PARAMETER = '📥'

    @classmethod
    def from_emoji(cls, emoji: str):
        for action_parameter in cls:
            if action_parameter.value == emoji:
                return action_parameter
        raise ValueError(f'No ActionParameter found for emoji: {emoji}')


class Action:

    def __init__(self, action_type: str | ActionType, action_parameter: dict):
        if isinstance(action_type, str):
            action_type = ActionType.from_emoji(action_type)
        self.action_type = action_type
        self.action_parameter = {}
        for k, v in action_parameter.items():
            if isinstance(k, str):
                k = ActionParameter.from_emoji(k)
            self.action_parameter[k] = v

    def __repr__(self):
        """Action Code"""
        return f"{self.action_type.value}{''.join(k.value + v for k, v in self.action_parameter.items())}{ActionType.END.value}"

    @classmethod
    def from_string(cls, action_code: str):
        emoji_match = emoji.emoji_list(action_code)
        assert emoji_match[-1][
                   'emoji'] == ActionType.END.value, f"Incomplete action code: action code {action_code} should end with {ActionType.END.value}"
        action_type = emoji_match[0]['emoji']
        action_parameter = {}
        parameter_values = []
        last_match_end = emoji_match[0]['match_start']
        for match in emoji_match:
            if match['match_start'] - last_match_end > 0:
                parameter_values.append(action_code[last_match_end: match['match_start']])
            last_match_end = match['match_end']
        for match, parameter_value in zip(emoji_match[1:-1], parameter_values):
            action_parameter[match['emoji']] = parameter_value
        return cls(action_type, action_parameter)


class ActionParser:
    """Parse LLM output token to action code"""

    def match(self, current_token: str, unprocessed_tokens: str) -> bool:
        raise NotImplementedError

    def parse(self, current_token: str, unprocessed_tokens: str) -> str:
        raise NotImplementedError

    def reset(self) -> None:
        ...


class SpeakActionParser(ActionParser):
    syntax = ActionType.SPEAK.value + ActionParameter.SPEAKER.value + "{speaker}" + ActionParameter.TEXT.value + "{text}"
    sentence_splits = ('.', '!', '?', '。', '！', '？')

    def __init__(self):
        self._speaker = None

    def match(self, current_token: str, unprocessed_tokens: str) -> bool:
        if self._speaker:
            return True
        elif ':' in unprocessed_tokens:
            self._speaker = unprocessed_tokens.split(':')[0]
            return True

    def parse(self, current_token: str, unprocessed_tokens: str) -> Action:
        if current_token == '' or set(current_token).intersection(self.sentence_splits):
            return Action(ActionType.SPEAK,
                          {ActionParameter.SPEAKER: self._speaker, ActionParameter.TEXT: unprocessed_tokens})
        return ''

    def reset(self) -> None:
        self._speaker = None


#
# class ToolParser(Parser):
#
#     def submit(self, token: str) -> None | Output:
#         if ToolSymbol.TOOL_NAME.value in token:
#             self.activate()
#         if self.is_active:
#             self.buffer += token
#             if ToolSymbol.TOOL_END.value in token:
#                 self.deactivate()
#         tool_calls = ToolCall.from_string(self.buffer)
#         for tool_call in tool_calls:
#             tool_call.tool.invoke(tool_call.tool_parameter)
#             return self.tokenizer.invoke(self.buffer)
#         self.buffer += token
#         return None


class ActionTranspiler(Runnable):
    """
    None: no action
    Callable: take instant action
    Future: submit to executor
    """

    def __init__(self, parsers: list[ActionParser]):
        self.parsers = parsers

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        result = ''
        for action_token in self.stream(input):
            result += action_token
        return result

    def stream(
            self,
            input: Input,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        for i in self.parsers:
            i.reset()
        unprocessed_tokens = ''
        current_active_parser = None
        for current_token in input:
            for parser in self.parsers:
                is_matched = parser.match(current_token, unprocessed_tokens)
                if is_matched:
                    if parser != current_active_parser and current_active_parser is not None:
                        action_code = current_active_parser.parse('', unprocessed_tokens)
                        if action_code:
                            unprocessed_tokens = ''
                        yield action_code
                    current_active_parser = parser
                    action_code = parser.parse(current_token, unprocessed_tokens)
                    if action_code:
                        unprocessed_tokens = ''
                    yield action_code
                    continue
            unprocessed_tokens += current_token


class ActionExecutor:
    action_type: ActionType
    num_workers: int = 1
    executor: Runnable
    evaluator: Callable

    def __init__(self, validator: Callable, executor: Runnable, evaluator: Callable, num_workers: int = 1):
        self.validator = validator
        self.execution_pool = ThreadPoolExecutor(max_workers=num_workers)
        self.executor = executor
        self.evaluator = evaluator

    def validate(self, action: Action) -> bool:
        return self.validator(action)

    def submit(self, action: Action) -> Future:
        return self.execution_pool.submit(self.executor.invoke, action.action_parameter)

    def evaluate(self, future: Future) -> Any:
        return self.evaluator(future.result())
