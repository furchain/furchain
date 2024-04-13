import enum
import re
from typing import Iterator, Union

import emoji
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import BaseTransformOutputParser

from furchain.interaction.tools import ToolSymbol


class ActionType(enum.Enum):
    SPEAK = '🗣️'
    DISPLAY = '🖼'
    SING = '🎤'
    TOOL = '🧰'
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
    TOOL_NAME = '🔨'
    TOOL_PARAMETER = '📥'
    TOOL_OUTPUT = '📤'

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
        self.callback = None

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

    def __init__(self, sentence_splits=('.', '!', '?', '。', '！', '？', '~')):
        self._speaker = None
        self.sentence_splits = sentence_splits

    def match(self, current_token: str, unprocessed_tokens: str) -> bool:
        if self._speaker:
            return True
        elif ':' in unprocessed_tokens:
            self._speaker = unprocessed_tokens.split(':')[0]
            return True

    def parse(self, current_token: str, unprocessed_tokens: str) -> Action:
        if current_token == '' or set(current_token).intersection(self.sentence_splits):
            if not unprocessed_tokens:
                return ''
            return Action(ActionType.SPEAK,
                          {ActionParameter.SPEAKER: self._speaker,
                           ActionParameter.TEXT: unprocessed_tokens.removeprefix(self._speaker + ':') + current_token})
        return ''

    def reset(self) -> None:
        self._speaker = None

class ToolActionParser(ActionParser):
    syntax = ActionType.TOOL.value + "{tool_name}" + ActionParameter.TOOL_PARAMETER.value + "{tool_parameter}" + ActionParameter.TOOL_OUTPUT.value

    def __init__(self):
        self._active = False

    def match(self, current_token: str, unprocessed_tokens: str) -> bool:
        if current_token == ToolSymbol.TOOL_NAME.value:
            self._active = True
            return True
        elif current_token == ToolSymbol.TOOL_END.value:
            self._active = False
            return True
        else:
            return self._active

    def parse(self, current_token: str, unprocessed_tokens: str) -> Action:
        if current_token == ActionType.END.value:
            pattern = f'''.*?{ActionParameter.TOOL_NAME.value}(.+?){ActionParameter.TOOL_PARAMETER.value}(.+?){ActionParameter.TOOL_OUTPUT.value}(.+?){ActionType.END.value}'''
            print(pattern, unprocessed_tokens + current_token)
            match = re.findall(pattern, unprocessed_tokens + current_token, re.DOTALL)[0]
            return Action(ActionType.TOOL, {
                ActionParameter.TOOL_NAME: match[0],
                ActionParameter.TOOL_PARAMETER: match[1],
                ActionParameter.TOOL_OUTPUT: match[2]})
        return ''


class ActionOutputParser(BaseTransformOutputParser):
    parsers: list[ActionParser]

    class Config:
        arbitrary_types_allowed = True

    def parse(self, text: str) -> str:
        return text

    def _transform(self, input: Iterator[Union[str, BaseMessage]]) -> Iterator[Action]:
        for i in self.parsers:
            i.reset()
        unprocessed_tokens = ''
        current_active_parser = None
        for current_token in input:
            # print(f"{current_token=}, {unprocessed_tokens=}")
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
                    else:
                        unprocessed_tokens += current_token
                    break
            else:
                unprocessed_tokens += current_token
