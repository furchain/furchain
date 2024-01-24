from typing import Optional, Any, Callable

from langchain_core.output_parsers import BaseCumulativeTransformOutputParser
from langchain_core.output_parsers.base import T
from translate import Translator


class ChineseTranslateStreamOutputParser(BaseCumulativeTransformOutputParser):
    diff = True

    def _diff(self, prev: Optional[T], next: T) -> T:
        if prev:
            sentence = next.removeprefix(prev)
        else:
            sentence = next
        translated_sentence = Translator(to_lang='zh-cn').translate(sentence)
        return translated_sentence

    def parse(self, text: str) -> T:
        return text

    def get_format_instructions(self) -> str:
        return ''


class CustomStreamOutputParser(BaseCumulativeTransformOutputParser):
    diff = True
    func: Callable

    def _diff(self, prev: Optional[T], next: T) -> T:
        if prev:
            sentence = next.removeprefix(prev)
        else:
            sentence = next
        return self.func(sentence)

    def parse(self, text: str) -> T:
        return text

    def get_format_instructions(self) -> str:
        return ''

    @property
    def _type(self) -> str:
        return "chinese_translate_stream_output_parser"


class SentenceStreamOutputParser(BaseCumulativeTransformOutputParser):
    diff = True
    splits = ('\n', '. ', '! ', '? ', '* ', '。', '？', '！')
    truncate_prefix = '### Response: '
    truncate_suffix = '</s>'
    min_length = 10
    done_sentence = ''
    current_sentence = ''

    def _diff(self, prev: Optional[Any], next: Any) -> Any:
        if next == '':
            last_sentence = self.current_sentence.removeprefix(self.truncate_prefix).removesuffix(self.truncate_suffix)
            return last_sentence
        for s in self.splits:
            if s in self.current_sentence:
                sentence, _ = self.current_sentence.rsplit(s, 1)
                if len(sentence) < self.min_length:
                    continue
                sentence += s
                self.done_sentence += sentence
                result = sentence.removeprefix(self.truncate_prefix).removesuffix(self.truncate_suffix)
                return result
        return ''

    def parse(self, text: str) -> T:
        if len(text) == len(self.done_sentence) + len(self.current_sentence):
            return ''
        self.current_sentence = text[len(self.done_sentence):]
        return text

    def get_format_instructions(self) -> str:
        return ''

    @property
    def _type(self) -> str:
        return "sentence_stream_output_parser"
