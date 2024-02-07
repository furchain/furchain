import abc
import enum

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompt_values import ChatPromptValue


class ChatFormatParser(metaclass=abc.ABCMeta):
    stop: list = list()

    @abc.abstractmethod
    def parse(self, chat_prompt_value: ChatPromptValue) -> str:
        raise NotImplementedError


class Llama2ChatFormatParser(ChatFormatParser):
    _sep = " "
    _sep2 = "</s>"
    _system_prefix = "<s>[INST] <<SYS>>\n"
    _system_suffix = "\n<</SYS>>"
    _human_prefix = "<s>[INST]"
    _ai_prefix = "[/INST]"
    stop = [_human_prefix, _sep2]

    @classmethod
    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        messages = chat_prompt_value.messages
        prompt = ''
        system_message = ''
        if len(messages) > 0 and isinstance(messages[0], SystemMessage):
            system_message = cls._system_prefix + messages[0].content + cls._system_suffix
            messages = messages[1:]
        prompt = system_message + cls._sep + prompt
        for idx, i in enumerate(messages):
            if isinstance(i, HumanMessage):
                prompt += cls._human_prefix + i.content + cls._sep2
            elif isinstance(i, AIMessage):
                prompt += cls._ai_prefix + i.content + cls._sep2
        prompt += cls._ai_prefix
        return prompt


class VicunaChatFormatParser(ChatFormatParser):
    _sep = " "
    _sep2 = "</s>"
    _system_message = "A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions."
    _human_prefix = "USER"
    _ai_prefix = "ASSISTANT"
    stop = [_ai_prefix, _sep2]

    @classmethod
    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        messages = chat_prompt_value.messages
        system_message = cls._system_message
        if len(messages) > 0 and isinstance(messages[0], SystemMessage):
            system_message = messages[0].content
            messages = messages[1:]
        prompt = system_message + cls._sep
        for idx, i in enumerate(messages):
            if isinstance(i, HumanMessage):
                prompt += cls._human_prefix + ": " + i.content + cls._sep2
            elif isinstance(i, AIMessage):
                prompt += cls._ai_prefix + ": " + i.content + cls._sep2
        prompt += cls._ai_prefix + ": "  # Append the AI prefix for the next response
        return prompt
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
        prompt += cls._ai_prefix
        return prompt


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
        return prompt


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
        return prompt


class ChatFormat(enum.Enum):
    Alpaca = 'Alpaca'
    ExtendedAlpaca = 'ExtendedAlpaca'
    LimaRPExtendedAlpaca = 'LimaRPExtendedAlpaca'
    ChatML = 'ChatML'
    Llama2 = 'Llama2'
    Vicuna = 'Vicuna'

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
        elif self == ChatFormat.Llama2:
            return Llama2ChatFormatParser()
        elif self == ChatFormat.Vicuna:
            return VicunaChatFormatParser()
        else:
            raise NotImplementedError
