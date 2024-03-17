import abc
import enum

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompt_values import ChatPromptValue


class ChatFormatParser(metaclass=abc.ABCMeta):
    """
    Abstract base class for chat format parsers.

    Attributes:
        stop (list): List of stop words or phrases.

    Methods:
        parse(chat_prompt_value: ChatPromptValue): Abstract method for parsing a chat prompt value.
    """
    stop: list = list()

    @abc.abstractmethod
    def parse(self, chat_prompt_value: ChatPromptValue) -> str:
        """
        Abstract method for parsing a chat prompt value.

        Args:
            chat_prompt_value (ChatPromptValue): The chat prompt value to parse.

        Returns:
            str: The parsed chat prompt value.

        Raises:
            NotImplementedError: This method must be implemented by a subclass.
        """
        raise NotImplementedError


class Llama2ChatFormatParser(ChatFormatParser):
    """
    Chat format parser for the Llama2 format.

    Attributes:
        _sep (str): Separator string.
        _sep2 (str): Secondary separator string.
        _system_prefix (str): Prefix for system messages.
        _system_suffix (str): Suffix for system messages.
        _human_prefix (str): Prefix for human messages.
        _ai_prefix (str): Prefix for AI messages.
        stop (list): List of stop words or phrases.

    Methods:
        parse(chat_prompt_value: ChatPromptValue): Parses a chat prompt value in the Llama2 format.
    """
    _sep = " "
    _sep2 = "</s>"
    _system_prefix = "<s>[INST] <<SYS>>\n"
    _system_suffix = "\n<</SYS>>"
    _human_prefix = "<s>[INST]"
    _ai_prefix = "[/INST]"
    stop = [_human_prefix, _sep2]

    @classmethod
    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        """
        Parses a chat prompt value in the Llama2 format.

        Args:
            chat_prompt_value (ChatPromptValue): The chat prompt value to parse.

        Returns:
            str: The parsed chat prompt value.
        """
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
    """
    Chat format parser for the Vicuna format.

    Attributes:
        _sep (str): Separator string.
        _sep2 (str): Secondary separator string.
        _system_message (str): Default system message.
        _human_prefix (str): Prefix for human messages.
        _ai_prefix (str): Prefix for AI messages.
        stop (list): List of stop words or phrases.

    Methods:
        parse(chat_prompt_value: ChatPromptValue): Parses a chat prompt value in the Vicuna format.
    """
    _sep = " "
    _sep2 = "</s>"
    _system_message = "A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions."
    _human_prefix = "USER"
    _ai_prefix = "ASSISTANT"
    stop = [_ai_prefix, _sep2]

    @classmethod
    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        """
        Parses a chat prompt value in the Vicuna format.

        Args:
            chat_prompt_value (ChatPromptValue): The chat prompt value to parse.

        Returns:
            str: The parsed chat prompt value.
        """
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
    """
    Chat format parser for the Alpaca format.

    Attributes:
        _sep (str): Separator string.
        _sep2 (str): Secondary separator string.
        _human_prefix (str): Prefix for human messages.
        _ai_prefix (str): Prefix for AI messages.
        stop (list): List of stop words or phrases.

    Methods:
        parse(chat_prompt_value: ChatPromptValue): Parses a chat prompt value in the Alpaca format.
    """

    _sep = "\n\n"
    _sep2 = "</s>"
    _human_prefix = "### Instruction:\n"
    _ai_prefix = "### Response:\n"
    stop = ['### Instruction:', _sep2]

    @classmethod
    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        """
        Parses a chat prompt value in the Alpaca format.

        Args:
            chat_prompt_value (ChatPromptValue): The chat prompt value to parse.

        Returns:
            str: The parsed chat prompt value.
        """
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
    """
    Chat format parser for the Extended Alpaca format.

    Attributes:
        _sep (str): Separator string.
        _human_prefix (str): Prefix for human messages.
        _ai_prefix (str): Prefix for AI messages.
        stop (list): List of stop words or phrases.

    Methods:
        parse(chat_prompt_value: ChatPromptValue): Parses a chat prompt value in the Extended Alpaca format.
    """

    _sep = '\n\n'
    _human_prefix = '### Input:\n'
    _ai_prefix = '### Response:\n'
    stop = ["### Input:", "### Response:", '\n#']

    @classmethod
    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        """
        Parses a chat prompt value in the Extended Alpaca format.

        Args:
            chat_prompt_value (ChatPromptValue): The chat prompt value to parse.

        Returns:
            str: The parsed chat prompt value.
        """
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
    """
    Chat format parser for the LimaRP Extended Alpaca format.

    Attributes:
        length (str): The length of the response. Default is 'medium'.

    Methods:
        parse(chat_prompt_value: ChatPromptValue): Parses a chat prompt value in the LimaRP Extended Alpaca format.
    """

    def __init__(self, length: str = 'medium'):
        super().__init__()
        self.length = length

    def parse(cls, chat_prompt_value: ChatPromptValue) -> str:
        """
        Parses a chat prompt value in the LimaRP Extended Alpaca format.

        Args:
            chat_prompt_value (ChatPromptValue): The chat prompt value to parse.

        Returns:
            str: The parsed chat prompt value.
        """
        prompt = super().parse(chat_prompt_value).removesuffix(
            '### Response:') + '### Response: (length = ' + cls.length + ')\n'
        return prompt


class ChatMLChatFormatParser(ChatFormatParser):
    """
    Chat format parser for the ChatML format.

    Attributes:
        _sep (str): Separator string used to separate different parts of the chat.
        _human_prefix (str): Prefix for user messages.
        _ai_prefix (str): Prefix for assistant messages.
        stop (list): List of stop words or phrases.

    Methods:
        parse(chat_prompt_value: ChatPromptValue): Parses a chat prompt value in the ChatML format.
    """

    _sep = "<|im_""end|>\n"  # This special token prevents copilot from generating complete response, so I split it into two parts
    _human_prefix = "<|im_start|>user\n"
    _ai_prefix = "<|im_start|>assistant\n"
    stop = ["<|im_""end|>"]

    @classmethod
    def parse(self, chat_prompt_value: ChatPromptValue) -> str:
        """
        Parses a chat prompt value in the ChatML format.

        Args:
            chat_prompt_value (ChatPromptValue): The chat prompt value to parse.

        Returns:
            str: The parsed chat prompt value.

        The method starts by initializing the prompt with a system message.
        Then it iterates over the messages in the chat prompt value.
        For each message, it checks the type of the message (HumanMessage or AIMessage) and appends the content of the message to the prompt with the appropriate prefix.
        Finally, it appends the AI prefix to the prompt and returns it.
        """
        messages = chat_prompt_value.messages
        prompt = "<|im_start|>system\n"
        system_message = ''
        if len(messages) > 0 and isinstance(messages[0], SystemMessage):
            system_message = messages[0].content
            messages = messages[1:]
        prompt = prompt + system_message + self._sep
        for idx, i in enumerate(messages):
            if isinstance(i, HumanMessage):
                prompt += self._human_prefix + i.content + self._sep
            elif isinstance(i, AIMessage):
                prompt += self._ai_prefix + i.content + self._sep
        prompt += self._ai_prefix  # + response_prefix
        return prompt


class QwenChatFormatParser(ChatMLChatFormatParser):
    """
    Chat format parser for the Qwen format.

    This class inherits from the ChatMLChatFormatParser and overrides the stop attribute.

    Attributes:
        stop (list): List of stop words or phrases. In this case, it's the end of text token.
    """
    stop = ["<|""endoftext|>"]

    @classmethod
    def parse(self, chat_prompt_value: ChatPromptValue) -> str:
        """
        Parses a chat prompt value in the ChatML format.

        Args:
            chat_prompt_value (ChatPromptValue): The chat prompt value to parse.

        Returns:
            str: The parsed chat prompt value.

        The method starts by initializing the prompt with a system message.
        Then it iterates over the messages in the chat prompt value.
        For each message, it checks the type of the message (HumanMessage or AIMessage) and appends the content of the message to the prompt with the appropriate prefix.
        Finally, it appends the AI prefix to the prompt and returns it.
        """
        messages = chat_prompt_value.messages
        prompt = "<|im_start|>system\n"
        system_message = ''
        if len(messages) > 0 and isinstance(messages[0], SystemMessage):
            system_message = messages[0].content
            messages = messages[1:]
        prompt = prompt + system_message + self._sep
        for idx, i in enumerate(messages):
            if isinstance(i, HumanMessage):
                prompt += self._human_prefix + i.content + self._sep
            elif isinstance(i, AIMessage):
                prompt += self._ai_prefix + i.content + self._sep
        prompt += self._ai_prefix  # + response_prefix
        return prompt


class ChatFormat(enum.Enum):
    """
    Enum for chat formats.

    Attributes:
        Alpaca (str): Alpaca chat format.
        ExtendedAlpaca (str): Extended Alpaca chat format.
        LimaRPExtendedAlpaca (str): LimaRP Extended Alpaca chat format.
        ChatML (str): ChatML chat format.
        Llama2 (str): Llama2 chat format.
        Vicuna (str): Vicuna chat format.
        Qwen (str): Qwen chat format.

    Methods:
        parser: Returns the appropriate chat format parser for the chat format.
    """

    Alpaca = 'Alpaca'
    ExtendedAlpaca = 'ExtendedAlpaca'
    LimaRPExtendedAlpaca = 'LimaRPExtendedAlpaca'
    ChatML = 'ChatML'
    Llama2 = 'Llama2'
    Vicuna = 'Vicuna'
    Qwen = 'Qwen'

    @property
    def parser(self) -> ChatFormatParser:
        """
        Returns the appropriate chat format parser for the chat format.

        Returns:
            ChatFormatParser: The chat format parser.
        """
        return {
            ChatFormat.Alpaca: AlpacaChatFormatParser,
            ChatFormat.ExtendedAlpaca: ExtendedAlpacaChatFormatParser,
            ChatFormat.LimaRPExtendedAlpaca: LimaRPExtendedAlpacaChatFormatParser,
            ChatFormat.ChatML: ChatMLChatFormatParser,
            ChatFormat.Llama2: Llama2ChatFormatParser,
            ChatFormat.Vicuna: VicunaChatFormatParser,
            ChatFormat.Qwen: QwenChatFormatParser
        }[self]()


__all__ = [
    "ChatFormat"
]
