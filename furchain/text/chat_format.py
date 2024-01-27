import abc
import enum

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompt_values import ChatPromptValue


class ChatFormatParser(metaclass=abc.ABCMeta):
    stop: list = list()

    @abc.abstractmethod
    def parse(self, chat_prompt_value: ChatPromptValue) -> str:
        raise NotImplementedError


class AlpacaChatFormatParser(ChatFormatParser):
    _sep = "\n\n"
    _sep2 = "</s>"
    _human_prefix = "### Instruction:\n"
    _ai_prefix = "### Response:\n"
    stop = ['### Instruction:', _sep2]

    @classmethod
    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        messages = chat_prompt_value.messages
        prompt = ''
        system_message = ''
        if len(messages) > 0 and isinstance(messages[0], SystemMessage):
            system_message = messages[0].content
            messages = messages[1:]
        prompt = system_message + cls._sep + prompt
        seps = [cls._sep, cls._sep2]
        for idx, i in enumerate(messages):
            if isinstance(i, HumanMessage):
                prompt += cls._human_prefix + i.content + seps[idx % 2]
            elif isinstance(i, AIMessage):
                prompt += cls._ai_prefix + i.content + seps[idx % 2]
        prompt += cls._ai_prefix  # + response_prefix
        return prompt.rstrip()


class ExtendedAlpacaChatFormatParser(ChatFormatParser):
    _sep = '\n\n'
    _human_prefix = '### Input:\n'
    _ai_prefix = '### Response:\n'
    stop = ["### Input:", "### Response:", '\n#']

    @classmethod
    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        messages = chat_prompt_value.messages
        prompt = '### Instruction:\n'
        system_message = ''
        if len(messages) > 0 and isinstance(messages[0], SystemMessage):
            system_message = messages[0].content
            messages = messages[1:]
        prompt = prompt + system_message + cls._sep
        for idx, i in enumerate(messages):
            if isinstance(i, HumanMessage):
                prompt += cls._human_prefix + i.content + cls._sep
            elif isinstance(i, AIMessage):
                prompt += cls._ai_prefix + i.content + cls._sep
        prompt += cls._ai_prefix  # .replace('\n', " (length = medium)\n") + response_prefix
        return prompt.rstrip()


class LimaRPExtendedAlpacaChatFormatParser(ExtendedAlpacaChatFormatParser):

    def __init__(self, length: str = 'medium'):
        super().__init__()
        self.length = length

    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        prompt = super().parse(chat_prompt_value).removesuffix(
            '### Response:') + '### Response: (length = ' + cls.length + ')\n'
        return prompt


class ChatMLChatFormatParser(ChatFormatParser):
    _sep = "<|im_end|>"
    _human_prefix = "<|im_start|>user"
    _ai_prefix = "<|im_start|>assistant"
    stop = ['<|im_end|>']

    @classmethod
    def parse(self, chat_prompt_value: ChatPromptValue) -> str:
        messages = chat_prompt_value.messages
        prompt = '<|im_start|>system'
        system_message = ''
        if len(messages) > 0 and isinstance(messages[0], SystemMessage):
            system_message = messages[0].content
            messages = messages[1:]
        prompt = system_message + self._sep + prompt
        for idx, i in enumerate(messages):
            if isinstance(i, HumanMessage):
                prompt += self._human_prefix + i.content + self._sep
            elif isinstance(i, AIMessage):
                prompt += self._ai_prefix + i.content + self._sep
        prompt += self._ai_prefix  # + response_prefix
        return prompt.rstrip()


class ChatFormat(enum.Enum):
    Alpaca = 'Alpaca'
    ExtendedAlpaca = 'ExtendedAlpaca'
    LimaRPExtendedAlpaca = 'LimaRPExtendedAlpaca'
    ChatML = 'ChatML'

    @property
    def parser(self) -> ChatFormatParser:
        if self == ChatFormat.Alpaca:
            return AlpacaChatFormatParser()
        elif self == ChatFormat.ExtendedAlpaca:
            return ExtendedAlpacaChatFormatParser()
        elif self == ChatFormat.LimaRPExtendedAlpaca:
            return LimaRPExtendedAlpacaChatFormatParser()
        elif self == ChatFormat.ChatML:
            return ChatMLChatFormatParser()
        else:
            raise NotImplementedError
