import enum
import json
import re
from abc import ABCMeta
from typing import Optional

from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Output


class ToolSymbol(enum.Enum):
    TOOL_NAME = "\U0001F528"  # "🔨"
    TOOL_PARAMETER = "\U0001F4E5"  # "📥"
    TOOL_OUTPUT = "\U0001F4E4"  # "📤"
    TOOL_END = "\U0001F51A"  # "🔚"


class ToolValidator(ABCMeta):
    def __new__(cls, name, bases, attrs):
        if name == "Tool":  # bypass validation for the base class
            return super().__new__(cls, name, bases, attrs)
        tool_name = attrs['tool_name']
        # grammar = attrs['grammar']

        assert re.search(r'^[a-z\-]+$', tool_name), "Tool name should be in lowercase and separated by hyphen"
        assert not re.search(
            "|".join([re.escape(i) for i in
                      [ToolSymbol.TOOL_NAME.value, ToolSymbol.TOOL_PARAMETER.value, ToolSymbol.TOOL_OUTPUT.value,
                       ToolSymbol.TOOL_END.value]]),
            tool_name), "Tool name should not contain any of the tool symbols"
        # assert LlamaGrammar.from_string(grammar, False), f"Grammar of {name} is not valid"
        # tool_name_grammar = tool_name + '-prefix ::= "' + ToolSymbol.TOOL_NAME.value.encode('unicode-escape').decode(
        #     'utf-8') + tool_name + ToolSymbol.TOOL_PARAMETER.value.encode('unicode-escape').decode('utf-8') + '"'
        # attrs['grammar'] = grammar.replace('root', tool_name, 1).replace("::=", f"::= {tool_name}-prefix",
        #                                                                  1) + '\n' + tool_name_grammar  # add tool name prefix to root to prevent name collision
        # TODO: add tool name prefix to other private non-terminal symbols while avoiding replacing terminals

        new_class = super().__new__(cls, name, bases, attrs)
        return new_class


class Tool(Runnable, metaclass=ToolValidator):
    tool_name: str  # "example-tool"
    tool_description: str  # "Example tool description, pass in an integer"
    tool_parameter_grammar: str  # r'''root ::= [0-9]+'''

    @classmethod
    def run(cls, **kwargs: Optional) -> Output:
        raise NotImplementedError

    @classmethod
    def invoke(cls, input: str, config: Optional = None) -> Output:
        raise NotImplementedError


class ToolCall(BaseModel):
    tool_name: str
    tool_parameter: str = "root ::= object"
    tool: Tool = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_string(cls, input: str) -> "ToolCall":
        pattern = ToolSymbol.TOOL_NAME.value + r'(.*?)' + ToolSymbol.TOOL_PARAMETER.value + r'(.*?)' + ToolSymbol.TOOL_OUTPUT.value
        match = re.findall(pattern, input, re.DOTALL)[-1]
        return (cls(tool_name=match[0], tool_parameter=match[1]))

    def execute(self) -> str:
        for tool in Tool.__subclasses__():
            if tool.tool_name == self.tool_name:
                self.tool = tool()
                break
        if self.tool is None:
            return "Tool not found"
        return self.tool.invoke(self.tool_parameter)


