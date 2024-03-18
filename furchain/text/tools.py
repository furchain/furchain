import enum
import json
import re
from abc import ABCMeta
from typing import Optional

from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Output
from llama_cpp.llama_grammar import LlamaGrammar

from furchain.text.grammars import JSON_GRAMMAR


class ToolSymbol(enum.Enum):
    TOOL_NAME = "\U0001F528"  # "🔨"
    TOOL_PARAMETER = "\U0001F4E5"  # "📥"
    TOOL_OUTPUT = "\U0001F4E4"  # "📤"
    # TOOL_END = "\U0001F3C1"  # "🏁"
    TOOL_END = "\U0001F6D1"  # 🛑


class ToolValidator(ABCMeta):
    def __new__(cls, name, bases, attrs):
        if name == "Tool":  # bypass validation for the base class
            return super().__new__(cls, name, bases, attrs)
        tool_name = attrs['tool_name']
        grammar = attrs['grammar']

        assert re.search(r'^[a-z\-]+$', tool_name), "Tool name should be in lowercase and separated by hyphen"
        assert not re.search(
            "|".join([re.escape(i) for i in
                      [ToolSymbol.TOOL_NAME.value, ToolSymbol.TOOL_PARAMETER.value, ToolSymbol.TOOL_OUTPUT.value,
                       ToolSymbol.TOOL_END.value]]),
            tool_name), "Tool name should not contain any of the tool symbols"
        assert LlamaGrammar.from_string(grammar, False), f"Grammar of {name} is not valid"
        tool_name_grammar = tool_name + '-prefix ::= "' + ToolSymbol.TOOL_NAME.value.encode('unicode-escape').decode(
            'utf-8') + tool_name + ToolSymbol.TOOL_PARAMETER.value.encode('unicode-escape').decode('utf-8') + '"'
        attrs['grammar'] = grammar.replace('root', tool_name, 1).replace("::=", f"::= {tool_name}-prefix",
                                                                         1) + '\n' + tool_name_grammar  # add tool name prefix to root to prevent name collision
        # TODO: add tool name prefix to other private non-terminal symbols while avoiding replacing terminals

        new_class = super().__new__(cls, name, bases, attrs)
        return new_class


class Tool(Runnable, metaclass=ToolValidator):
    tool_name: str  # "example-tool"
    tool_description: str  # "Example tool description, pass in an integer"
    grammar: str  # r'''root ::= [0-9]+'''

    def run(self, **kwargs: Optional) -> Output:
        raise NotImplementedError

    def invoke(self, input: str, config: Optional = None) -> Output:
        raise NotImplementedError


class ToolCall(BaseModel):
    tool_name: str
    tool_parameter: str
    tool: Tool = None
    source: str

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_string(cls, input: str) -> list["ToolCall"]:
        tool_calls = []
        pattern = "(" + ToolSymbol.TOOL_NAME.value + r'(.*?)' + ToolSymbol.TOOL_PARAMETER.value + r'(.*?))(?=' + ToolSymbol.TOOL_NAME.value + r'|' + ToolSymbol.TOOL_END.value + ')'
        matches = re.findall(pattern, input, re.DOTALL)
        for match in matches:
            tool_calls.append(cls(source=match[0], tool_name=match[1], tool_parameter=match[2]))
        for tool_call in tool_calls:
            for tool in Tool.__subclasses__():
                if tool.tool_name == tool_call.tool_name.strip():
                    tool_call.tool = tool()
                    break
        return tool_calls

    def execute(self) -> str:
        if self.tool is None:
            return "Tool not found"
        return self.tool.invoke(self.tool_parameter)


class DrawImageTool(Tool):
    tool_name = "draw-image"
    tool_description = '''Useful when you need to draw an image. Parameter: "prompt" as string. Output: path to generated image.'''
    grammar = JSON_GRAMMAR  # r'''root ::= "{\"prompt\": " "\"" [^\U0001F528\U0001F3C1\U0001F4E4]* "\""  "}"'''

    def run(self, prompt: str) -> Output:
        return f"Image saved at /data/{prompt}.png "

    def invoke(self, input: str, config: Optional = None) -> Output:
        param = json.loads(input)
        return self.run(**param)
