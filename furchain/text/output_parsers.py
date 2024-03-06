from typing import Optional, Any

from langchain_core.output_parsers import BaseCumulativeTransformOutputParser
from langchain_core.output_parsers.base import T


class SentenceStreamOutputParser(BaseCumulativeTransformOutputParser):
    """
    An output parser for streaming sentences.

    Attributes:
        diff (bool): A flag indicating whether to calculate the difference between the previous and next values.
        splits (tuple): The characters to split the sentences on.
        min_length (int): The minimum length of a sentence.
        done_sentence (str): The completed sentence.
        current_sentence (str): The current sentence.

    Methods:
        _diff(prev: Optional[Any], next: Any) -> Any: Returns the difference between the previous and next values.
        parse(text: str) -> T: Parses the text.
        get_format_instructions() -> str: Returns the format instructions.
    """
    diff = True
    splits = ('\n', '. ', '! ', '? ', '* ', '。', '？', '！')
    min_length = 10
    done_sentence = ''
    current_sentence = ''

    def _diff(self, prev: Optional[Any], next: Any) -> Any:
        """
        Returns the difference between the previous and next values.

        Args:
            prev (Optional[Any]): The previous value.
            next (Any): The next value.

        Returns:
            Any: The difference between the previous and next values.
        """
        if next == '':
            last_sentence = self.current_sentence
            self.current_sentence = ''
            return last_sentence
        for s in self.splits:
            if s in self.current_sentence:
                sentence, _ = self.current_sentence.rsplit(s, 1)
                if len(sentence) < self.min_length:
                    continue
                sentence += s
                self.done_sentence += sentence
                result = sentence
                return result
        return ''

    def parse(self, text: str) -> T:
        """
        Parses the text.

        Args:
            text (str): The text to parse.

        Returns:
            T: The parsed text.
        """
        if len(text) == len(self.done_sentence) + len(self.current_sentence):
            return ''
        self.current_sentence = text[len(self.done_sentence):]
        return text

    def get_format_instructions(self) -> str:
        """
        Returns the format instructions.

        Returns:
            str: The format instructions.
        """
        return ''

    @property
    def _type(self) -> str:
        """
        Returns the type of the output parser.

        Returns:
            str: The type of the output parser.
        """
        return "sentence_stream_output_parser"


__all__ = [
    "SentenceStreamOutputParser"
]
