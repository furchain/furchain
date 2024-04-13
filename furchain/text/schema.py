import itertools
import json
from typing import Optional, Any, Iterable, Iterator

import requests
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import SystemMessage, messages_from_dict
from langchain_core.messages import messages_to_dict
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import AIMessagePromptTemplate, \
    MessagesPlaceholder
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.pydantic_v1 import BaseModel as BaseModel_v1, Field as Field_v1, root_validator
from langchain_core.runnables import Runnable, RunnableBinding
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.utils import Output
from llama_cpp.llama_grammar import json_schema_to_gbnf, LlamaGrammar
from pydantic import BaseModel, Field
from pymongo import MongoClient

from furchain.config import TextConfig
from furchain.interaction.tools import ToolSymbol, Tool, ToolCall
from furchain.text.callbacks import StrChunkCallbackIterator
from furchain.text.chat_format import ChatFormat
from furchain.text.chat_message_history import MongoDBChatMessageHistory, logger
from furchain.text.chat_prompt_templates import ROLEPLAY_CHAT_PROMPT_TEMPLATE, NO_HISTORY_CHAT_PROMPT_TEMPLATE, \
    ROLEPLAY_WITH_TOOLS_CHAT_PROMPT_TEMPLATE
from furchain.text.grammars import JSON_GRAMMAR
from furchain.text.llama_cpp_client import LlamaCppClient

CLASS_DICT = {
    'HumanMessagePromptTemplate': HumanMessagePromptTemplate,
    'AIMessagePromptTemplate': AIMessagePromptTemplate,
    'SystemMessagePromptTemplate': SystemMessagePromptTemplate,
    'HumanMessage': HumanMessage,
    'AIMessage': AIMessage,
    'SystemMessage': SystemMessage,
    'MessagesPlaceholder': MessagesPlaceholder
}


class Meta_v2(BaseModel):
    """
    A Pydantic model for meta data.

    Attributes:
        tags (list[str]): A list of tags for the meta data.
    """
    tags: list[str] = Field(default_factory=list, description="The tags of the meta data")


class _Scenario_v2(BaseModel):
    """
    A Pydantic model for scenario data used to generate GBNF grammar.

    Attributes:
        scenario_name (str): The name of the scenario.
        scenario_description (str): The description of the scenario.
        meta (Meta_v2): The meta data of the scenario.
        type (str): The type of the scenario.
    """
    scenario_name: str = Field(description="The name of the scenario")
    scenario_description: str = Field(description="The description of the scenario")
    meta: Meta_v2 = Field(default_factory=Meta_v2, description="The meta data of the scenario")
    type: str = "scenario"


class Scenario(BaseModel_v1):
    """
    A Pydantic model for scenario data.

    Attributes:
        scenario_name (str): The name of the scenario.
        scenario_description (str): The description of the scenario.
        meta (dict): The meta data of the scenario.
        type (str): The type of the scenario.

    Methods:
        create(description: str, llm): Creates a scenario.
        from_mongo(scenario_name: str, mongo_url: str, mongo_db: str, mongo_collection: str): Retrieves a scenario from MongoDB.
        to_mongo(mongo_url: str, mongo_db: str, mongo_collection: str): Stores a scenario in MongoDB.
        from_url(url: str): Retrieves a scenario from a URL.
        from_file(file_path: str): Retrieves a scenario from a file.
        to_dict() -> dict: Returns a dictionary representation of the scenario.
        to_json() -> str: Returns a JSON representation of the scenario.
        to_file(file_path: str): Stores a scenario in a file.
        from_dict(data: dict): Creates a scenario from a dictionary.
    """
    scenario_name: str = Field_v1(description="The name of the scenario")
    scenario_description: str = Field_v1(description="The description of the scenario")
    meta: dict = Field_v1(default_factory=dict, description="The meta data of the scenario")
    type: str = "scenario"

    @classmethod
    def create(cls, description: str, llm):
        """
        Creates a scenario.

        Args:
            description (str): The description of the scenario.
            llm: The LlamaCpp instance.

        Returns:
            Scenario: The created scenario.
        """
        return CreateScenarioByChat.create(description, llm)

    @classmethod
    def from_mongo(cls, scenario_name: str, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None):
        """
        Retrieves a scenario from MongoDB.

        Args:
            scenario_name (str): The name of the scenario.
            mongo_url (str, optional): The MongoDB URL. Defaults to None.
            mongo_db (str, optional): The MongoDB database name. Defaults to None.
            mongo_collection (str, optional): The MongoDB collection name. Defaults to None.

        Returns:
            Scenario: The retrieved scenario.
        """
        if mongo_url is None:
            mongo_url = TextConfig.get_mongo_url()
        if mongo_db is None:
            mongo_db = TextConfig.get_mongo_db()
        if mongo_collection is None:
            mongo_collection = TextConfig.get_mongo_scenario_collection()
        client = MongoClient(mongo_url)
        return cls.from_dict(
            client[mongo_db][mongo_collection].find_one({'scenario_name': scenario_name, 'type': "scenario"}))

    def to_mongo(self, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None):
        """
        Stores a scenario in MongoDB.

        Args:
            mongo_url (str, optional): The MongoDB URL. Defaults to None.
            mongo_db (str, optional): The MongoDB database name. Defaults to None.
            mongo_collection (str, optional): The MongoDB collection name. Defaults to None.

        Returns:
            UpdateResult: The result of the update operation.
        """
        if mongo_url is None:
            mongo_url = TextConfig.get_mongo_url()
        if mongo_db is None:
            mongo_db = TextConfig.get_mongo_db()
        if mongo_collection is None:
            mongo_collection = TextConfig.get_mongo_scenario_collection()
        client = MongoClient(mongo_url)
        document = self.to_dict()
        client[mongo_db][mongo_collection].create_index("type")
        return client[mongo_db][mongo_collection].update_one({"scenario_name": self.scenario_name}, {
            "$set": {"type": self.type,
                     "scenario_description": document["scenario_description"],
                     "meta": document["meta"]}}, upsert=True)

    @classmethod
    def from_url(cls, url: str):
        """
        Retrieves a scenario from a URL.

        Args:
            url (str): The URL.

        Returns:
            Scenario: The retrieved scenario.
        """
        return cls.from_dict(requests.get(url).json())

    @classmethod
    def from_file(cls, file_path: str):
        """
        Retrieves a scenario from a file.

        Args:
            file_path (str): The file path.

        Returns:
            Scenario: The retrieved scenario.
        """
        with open(file_path, 'r') as f:
            return cls.from_dict(json.load(f))

    def to_dict(self):
        """
        Returns a dictionary representation of the scenario.

        Returns:
            dict: A dictionary representation of the scenario.
        """
        return {
            "scenario_name": self.scenario_name,
            "scenario_description": self.scenario_description,
            "meta": self.meta
        }

    def to_json(self) -> str:
        """
        Returns a JSON representation of the scenario.

        Returns:
            str: A JSON representation of the scenario.
        """
        return json.dumps(self.to_dict())

    def to_file(self, file_path: str):
        """
        Stores a scenario in a file.

        Args:
            file_path (str): The file path.
        """
        with open(file_path, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict):
        """
        Creates a scenario from a dictionary.

        Args:
            data (dict): The data dictionary.

        Returns:
            Scenario: The created scenario.
        """
        data = data.copy()

        return Scenario(
            scenario_name=data['scenario_name'],
            scenario_description=data['scenario_description'],
            meta=Meta_v2(**data['meta'])
        )


class _Character_v2(BaseModel):
    """
    A Pydantic model for character data used to generate GBNF grammar.

    Attributes:
        character_name (str): The name of the character.
        persona (str): The persona of the character.
        meta (Meta_v2): The meta data of the character.
        type (str): The type of the character.
    """
    character_name: str = Field(description="The name of the character")
    persona: str = Field(description="The persona of the character")
    meta: Meta_v2 = Field(default_factory=Meta_v2, description="The meta data of the character")
    type: str = "character"


class Character(BaseModel_v1):
    """
    A Pydantic model for character data.

    Attributes:
        character_name (str): The name of the character.
        persona (str): The persona of the character.
        meta (dict): The meta data of the character.
        type (str): The type of the character.

    Methods:
        create(cls, description: str, llm): Creates a character.
        from_mongo(cls, character_name: str, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None): Retrieves a character from MongoDB.
        to_mongo(self, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None): Stores a character in MongoDB.
        from_url(cls, url: str): Retrieves a character from a URL.
        from_file(cls, file_path: str): Retrieves a character from a file.
        to_dict(self) -> dict: Returns a dictionary representation of the character.
        to_json(self) -> str: Returns a JSON representation of the character.
        to_file(self, file_path: str): Stores a character in a file.
        from_dict(cls, data: dict): Creates a character from a dictionary.
    """
    character_name: str = Field_v1(description="The name of the character")
    persona: str = Field_v1(description="The persona of the character")
    meta: dict = Field_v1(default_factory=dict, description="The meta data of the character")
    type: str = "character"

    @classmethod
    def create(cls, description: str, llm):
        """
        Creates a character.

        Args:
            description (str): The description of the character.
            llm: The LlamaCpp instance.

        Returns:
            Character: The created character.
        """
        return CreateCharacterByChat.create(description, llm)

    @classmethod
    def from_mongo(cls, character_name: str, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None):
        """
        Retrieves a character from MongoDB.

        Args:
            character_name (str): The name of the character.
            mongo_url (str, optional): The MongoDB URL. Defaults to None.
            mongo_db (str, optional): The MongoDB database name. Defaults to None.
            mongo_collection (str, optional): The MongoDB collection name. Defaults to None.

        Returns:
            Character: The retrieved character.
        """
        if mongo_url is None:
            mongo_url = TextConfig.get_mongo_url()
        if mongo_db is None:
            mongo_db = TextConfig.get_mongo_db()
        if mongo_collection is None:
            mongo_collection = TextConfig.get_mongo_character_collection()
        client = MongoClient(mongo_url)
        return cls.from_dict(
            client[mongo_db][mongo_collection].find_one({'character_name': character_name, "type": "character"}))

    def to_mongo(self, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None):
        """
        Stores a character in MongoDB.

        Args:
            mongo_url (str, optional): The MongoDB URL. Defaults to None.
            mongo_db (str, optional): The MongoDB database name. Defaults to None.
            mongo_collection (str, optional): The MongoDB collection name. Defaults to None.

        Returns:
            UpdateResult: The result of the update operation.
        """
        if mongo_url is None:
            mongo_url = TextConfig.get_mongo_url()
        if mongo_db is None:
            mongo_db = TextConfig.get_mongo_db()
        if mongo_collection is None:
            mongo_collection = TextConfig.get_mongo_character_collection()
        client = MongoClient(mongo_url)
        client[mongo_db][mongo_collection].create_index("type")
        document = self.to_dict()
        return client[mongo_db][mongo_collection].update_one({"character_name": self.character_name}, {
            "$set": {"persona": document["persona"],
                     "meta": document["meta"],
                     "type": self.type}}, upsert=True)

    @classmethod
    def from_url(cls, url: str):
        """
        Retrieves a character from a URL.

        Args:
            url (str): The URL.

        Returns:
            Character: The retrieved character.
        """
        return cls.from_dict(requests.get(url).json())

    @classmethod
    def from_file(cls, file_path: str):
        """
        Retrieves a character from a file.

        Args:
            file_path (str): The file path.

        Returns:
            Character: The retrieved character.
        """
        with open(file_path, 'r') as f:
            return cls.from_dict(json.load(f))

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the character.

        Returns:
            dict: A dictionary representation of the character.
        """
        return {
            "character_name": self.character_name,
            "persona": self.persona,
            "meta": self.meta,
        }

    def to_json(self) -> str:
        """
        Returns a JSON representation of the character.

        Returns:
            str: A JSON representation of the character.
        """
        return json.dumps(self.to_dict())

    def to_file(self, file_path: str):
        """
        Stores a character in a file.

        Args:
            file_path (str): The file path.
        """
        with open(file_path, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict):
        """
        Creates a character from a dictionary.

        Args:
            data (dict): The data dictionary.

        Returns:
            Character: The created character.
        """
        return Character(
            character_name=data['character_name'],
            persona=data['persona'],
            meta=data['meta'],
        )


class LlamaCpp(Runnable):
    """
    A class that represents a LlamaCpp runnable.

    Attributes:
        client (LlamaCppClient): The LlamaCpp client.
        chat_format (ChatFormat): The chat format.
        model_kwargs (dict): The model keyword arguments.

    Methods:
        invoke(input: str | list | dict, config: Optional[RunnableConfig] = None, **kwargs) -> Output: Invokes the LlamaCpp client with the given input and returns the output.
        stream(input: str | list | dict, config: Optional[RunnableConfig] = None, **kwargs: Optional[Any]) -> Iterator[Output]: Streams the LlamaCpp client with the given input and yields the output.
    """

    def __init__(self, base_url=None, api_key=None, chat_format: ChatFormat = ChatFormat.Alpaca, **kwargs):
        self.client = LlamaCppClient(base_url, api_key)
        self.chat_format = chat_format
        self.model_kwargs = kwargs

    def invoke(self, input: str | list | dict, config: Optional[RunnableConfig] = None, **kwargs) -> Output:
        """
        Invokes the LlamaCpp client with the given input and returns the output.

        Args:
            input (str | list | dict): The input to invoke the LlamaCpp client with.
            config (Optional[RunnableConfig]): The runnable config. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            Output: The output from the LlamaCpp client.
        """
        if isinstance(input, ChatPromptValue):
            input = self.chat_format.parser.parse(input)
        if isinstance(input, (str, list)):
            input = {"prompt": input}
        response = self.client.complete(input, **kwargs, **self.model_kwargs)
        logger.debug(response)
        return response['content']

    def stream(
            self,
            input: str | list | dict,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        """
        Streams the LlamaCpp client with the given input and yields the output.

        Args:
            input (str | list | dict): The input to stream the LlamaCpp client with.
            config (Optional[RunnableConfig]): The runnable config. Defaults to None.
            **kwargs: Additional keyword arguments.

        Yields:
            Output: The output from the LlamaCpp client.
        """
        if isinstance(input, ChatPromptValue):
            input = self.chat_format.parser.parse(input)
        if isinstance(input, (str, list)):
            input = {"prompt": input}
        for i in self.client.stream(input, **kwargs, **self.model_kwargs):
            yield i['content']


class Session(BaseModel_v1):
    """
    A class that represents a session.

    Attributes:
        session_id (str): The id of the session.
        npc (Character): The non-player character.
        player (Character): The player character.
        scenario (Scenario): The scenario.
        collection_name (str): The collection name.
        chat_history_proxy (MongoDBChatMessageHistory): The chat history proxy.

    Methods:
        create(description: str, llm: LlamaCpp, session_id=None, collection_name="Session"): Creates a session.
        from_mongo(session_id: str, collection_name: str = "Session"): Retrieves a session from MongoDB.
        to_dict() -> dict: Returns a dictionary representation of the session.
        from_dict(data: dict, session_id=None, collection_name="Session"): Creates a session from a dictionary.
        from_file(file_path: str, session_id=None, collection_name="Session"): Retrieves a session from a file.
        to_file(file_path: str): Stores a session in a file.
        messages: Returns the messages of the session.
        add_messages(messages): Adds messages to the session.
        add_message(message): Adds a message to the session.
        clear(): Clears the session.
    """
    session_id: str = Field_v1(None, description="The id of the session")
    npc: Character = Field_v1(Character(character_name=TextConfig.get_npc_name(),
                                        persona=TextConfig.get_npc_persona()),
                              description="Characteristics of the npc")
    player: Character = Field_v1(Character(character_name=TextConfig.get_player_name(),
                                           persona=TextConfig.get_player_persona()),
                                 description="Characteristics of the player")
    scenario: Scenario = Field_v1(Scenario(scenario_name="default",
                                           scenario_description=TextConfig.get_scenario_description()),
                                  description="Characteristics of the scenario")
    collection_name: str = "Session"
    chat_history_proxy: MongoDBChatMessageHistory = None

    class Config:
        arbitrary_types_allowed = True

    @root_validator
    def bind_chat_history_proxy(cls, values):
        """
        Binds the chat history proxy to the session.

        Args:
            values (dict): The values of the session.

        Returns:
            dict: The values of the session with the chat history proxy bound.
        """
        values['chat_history_proxy'] = MongoDBChatMessageHistory(
            connection_string=TextConfig.get_mongo_url(),
            database_name=TextConfig.get_mongo_db(),
            collection_name=values['collection_name'],
        ).bind(session_id=values['session_id'], npc=values['npc'], player=values['player'], scenario=values['scenario'])
        return values

    @classmethod
    def create(cls, description: str, llm: LlamaCpp, session_id=None, collection_name="Session"):
        """
        Creates a session.

        Args:
            description (str): The description of the session.
            llm (LlamaCpp): The LlamaCpp instance.
            session_id (str, optional): The id of the session. Defaults to None.
            collection_name (str, optional): The collection name. Defaults to "Session".

        Returns:
            Session: The created session.
        """
        return CreateSessionByChat.create(description=description, llm=llm, session_id=session_id,
                                          collection_name=collection_name)

    @classmethod
    def from_mongo(cls, session_id: str, collection_name: str = "Session"):
        """
        Retrieves a session from MongoDB.

        Args:
            session_id (str): The id of the session.
            collection_name (str, optional): The collection name. Defaults to "Session".

        Returns:
            Session: The retrieved session.
        """
        chat_history_proxy = MongoDBChatMessageHistory(
            connection_string=TextConfig.get_mongo_url(),
            database_name=TextConfig.get_mongo_db(),
            collection_name=collection_name,
        )
        result = chat_history_proxy.find(session_id=session_id, collection_name=collection_name)
        if result is None:
            return None
        else:
            npc = Character.from_dict(result['npc'])
            player = Character.from_dict(result['player'])
            scenario = Scenario.from_dict(result['scenario'])
            return cls(
                session_id=session_id,
                npc=npc,
                player=player,
                scenario=scenario,
                collection_name=collection_name
            )

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the session.

        Returns:
            dict: A dictionary representation of the session.
        """
        result = self.chat_history_proxy.dict()
        result.pop("_id", None)
        return result

    @classmethod
    def from_dict(cls, data: dict, session_id=None, collection_name="Session"):
        """
        Creates a session from a dictionary.

        Args:
            data (dict): The data dictionary.
            session_id (str, optional): The id of the session. Defaults to None.
            collection_name (str, optional): The collection name. Defaults to "Session".

        Returns:
            Session: The created session.
        """
        if session_id is not None:
            data['session_id'] = session_id
        session = cls(
            session_id=data['session_id'],
            npc=Character.from_dict(data['npc']),
            player=Character.from_dict(data['player']),
            scenario=Scenario.from_dict(data['scenario']),
            collection_name=collection_name
        )
        session.chat_history_proxy.chat_history = data.get("chat_history", [])
        return session

    @classmethod
    def from_file(cls, file_path: str, session_id=None, collection_name="Session"):
        """
        Retrieves a session from a file.

        Args:
            file_path (str): The file path.
            session_id (str, optional): The id of the session. Defaults to None.
            collection_name (str, optional): The collection name. Defaults to "Session".

        Returns:
            Session: The retrieved session.
        """
        with open(file_path, 'r') as f:
            return cls.from_dict(json.load(f), session_id, collection_name)

    def to_file(self, file_path: str):
        """
        Stores a session in a file.

        Args:
            file_path (str): The file path.
        """
        with open(file_path, 'w') as f:
            f.write(json.dumps(self.to_dict()))

    @property
    def messages(self):
        """
        Returns the messages of the session.

        Returns:
            list: The messages of the session.
        """
        return self.chat_history_proxy.messages

    def add_messages(self, messages) -> None:
        """
        Adds multiple messages to the session's chat history.

        Args:
            messages (list): The list of messages to be added.

        Returns:
            None
        """
        self.chat_history_proxy.add_messages(messages)

    def add_message(self, message) -> None:
        """
        Adds a single message to the session's chat history.

        Args:
            message (Message): The message to be added.

        Returns:
            None
        """
        self.chat_history_proxy.add_message(message)

    def clear(self) -> None:
        """
        Clears the session's chat history.

        Returns:
            None
        """
        self.chat_history_proxy.clear()


class Chat(Runnable):
    """
    A class that represents a chat in a role-playing game.

    Attributes:
        llm (LlamaCpp | RunnableBinding): The LlamaCpp instance or a RunnableBinding.
        session (Session): The session.
        chat_prompt_template (ChatPromptTemplate): The chat prompt template.
        grammar (str): The grammar.
        kwargs (dict): Additional keyword arguments.

    Methods:
        _get_chain_params(query: str, **kwargs): Gets the chain parameters.
        invoke(input: dict | str, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output: Invokes the chat with the given input and returns the output.
        stream(input: dict | str, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Iterable[Output]: Streams the chat with the given input and yields the output.
    """

    def __init__(self, llm: LlamaCpp | RunnableBinding,
                 session: Session,
                 chat_prompt_template: ChatPromptTemplate = None,
                 grammar: str = None,
                 tools: list[Tool] = None,
                 **kwargs):
        super().__init__()

        if grammar is None:
            self.grammar = r'''root ::= "''' + session.npc.character_name.encode("unicode-escape").decode(
                "utf-8") + r''':" [\u4E00-\u9FFFA-Za-z0-9\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E\uFF01-\uFF0F\uFF1A-\uFF20\uFF3B-\uFF40\uFF5B-\uFF65\u3002\n ]*'''  # Start with the npc's name, followed by any characters
        else:
            self.grammar = grammar
        if isinstance(llm, RunnableBinding):
            model_kwargs = llm.kwargs
            llm = llm.bound
        else:
            model_kwargs = llm.model_kwargs
        chat_format = llm.chat_format
        self.kwargs = kwargs
        self.tools = tools
        chat_format_parser = chat_format.parser if isinstance(chat_format, ChatFormat) else ChatFormat(
            chat_format).parser
        if self.tools:
            root_grammar = f'''root ::= "{session.npc.character_name.encode("unicode-escape").decode("utf-8")}:" ''' + f'''anything+ (tool | anything)+\n''' + f'''tool ::= {" | ".join(i.tool_name + "-root" for i in self.tools)}\n''' + r'''anything ::= [\u4E00-\u9FFFA-Za-z0-9\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E\uFF01-\uFF0F\uFF1A-\uFF20\uFF3B-\uFF40\uFF5B-\uFF65\u3002\n ]'''
            tool_grammar = '\n'.join([
                f'''{i.tool_name}-root ::= "{ToolSymbol.TOOL_NAME.value.encode("unicode-escape").decode("utf-8")}" "{i.tool_name}" "{ToolSymbol.TOOL_PARAMETER.value.encode("unicode-escape").decode("utf-8")}" parameter-{i.tool_name}-root "{ToolSymbol.TOOL_OUTPUT.value.encode("unicode-escape").decode("utf-8")}"'''
                for i in self.tools])
            json_grammar = "json-" + JSON_GRAMMAR
            parameter_grammar = '\n'.join([f'parameter-{i.tool_name}-' + i.tool_parameter_grammar for i in self.tools])
            self.grammar = '\n'.join([
                root_grammar,
                tool_grammar,
                json_grammar,
                parameter_grammar
            ])
        self.llm = llm.bind(stop=model_kwargs.get("stop", []) + chat_format_parser.stop, grammar=self.grammar)
        self.chat_format_parser = chat_format_parser
        self.session = session
        assert LlamaGrammar.from_string(self.grammar)

        if chat_prompt_template is None:
            if self.tools:
                self.chat_prompt_template = ROLEPLAY_WITH_TOOLS_CHAT_PROMPT_TEMPLATE
            else:
                self.chat_prompt_template = ROLEPLAY_CHAT_PROMPT_TEMPLATE
        else:
            self.chat_prompt_template = chat_prompt_template

    def _get_chain_params(self, query: str,
                          **kwargs):
        """
        Gets the chain parameters.

        Args:
            query (str): The query.
            **kwargs: Additional keyword arguments.

        Returns:
            tuple: The chain, parameters, and the function to update the chat history.
        """

        # Define the chain of operations
        prompt_template = (
                RunnableLambda(lambda x: (
                    self.chat_prompt_template.format_prompt(chat_history=messages_from_dict(x.pop('chat_history', [])),
                                                            **x)
                ))
                | RunnableLambda(self.chat_format_parser.parse)
        )
        if "chat_history" in self.chat_prompt_template.input_variables:
            history_messages = self.session.messages
        else:
            history_messages = []
        for i in history_messages:
            if isinstance(i, HumanMessage):
                i.content = i.content.removeprefix(f"{self.session.player.character_name}:")
                i.content = f"{self.session.player.character_name}:{i.content}"
            elif isinstance(i, AIMessage):
                i.content = i.content.removeprefix(f"{self.session.npc.character_name}:")
                i.content = f"{self.session.npc.character_name}:{i.content}"
        chat_history = messages_to_dict(history_messages)
        kwargs['npc_name'] = self.session.npc.character_name
        kwargs['npc_persona'] = self.session.npc.persona.format(
            npc_name=self.session.npc.character_name,
            player_name=self.session.player.character_name)
        kwargs['player_persona'] = self.session.player.persona.format(
            npc_name=self.session.npc.character_name,
            player_name=self.session.player.character_name)
        kwargs['player_name'] = self.session.player.character_name
        kwargs['scenario_description'] = self.session.scenario.scenario_description.format(
            npc_name=self.session.npc.character_name,
            player_name=self.session.player.character_name)
        kwargs['query'] = query
        kwargs['chat_history'] = chat_history
        if self.tools:
            kwargs['tools'] = "\n".join([f"{i.tool_name}: {i.tool_description}" for i in self.tools])

        def _update_chat_history(response):
            """
            Updates the chat history.

            Args:
                response (str): The response from AI.

            Returns:
                None
            """
            human_message = HumanMessage(content=f"{query}")
            ai_message = AIMessage(content=f"{response}")
            self.session.add_messages([
                human_message,
                ai_message
            ])

        return prompt_template, kwargs, _update_chat_history

    def invoke(
            self, input: dict | str, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> Output:
        """
        Invokes the chat with the given input and returns the output.

        Args:
            input (dict | str): The input to invoke the chat with.
            config (Optional[RunnableConfig]): The runnable config. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            Output: The output from the chat.
        """
        stream = self.stream(input, config, **kwargs)
        result = ''
        for i in stream:
            result += i
        return result

    def stream(
            self,
            input: dict | str,
            config: Optional[RunnableConfig] = None,
            **kwargs: Any
    ) -> Iterable[Output]:
        """
        Streams the chat with the given input and yields the output.

        Args:
            input (dict | str): The input to stream the chat with.
            config (Optional[RunnableConfig]): The runnable config. Defaults to None.
            **kwargs: Additional keyword arguments.

        Yields:
            Output: The output from the chat.
        """
        params = {}
        if isinstance(input, str):
            input = {'query': input}
        params.update(input)
        params.update(kwargs)
        prompt_template, params, _update_chat_history = self._get_chain_params(**params)
        prompt_template: ChatPromptTemplate
        chain = prompt_template | self.llm
        stream = chain.stream(params)
        logger.debug(f"stream input: {params}")
        if not self.tools:
            yield from StrChunkCallbackIterator(
                iterable=stream,
                callbacks=[_update_chat_history],
            )
        else:
            #
            def _stream(prompt_value, llm, buffer, content=''):
                logger.debug(f"stream input: {prompt_value}")
                new_stream = llm.stream(prompt_value)
                iterator = StrChunkCallbackIterator(
                    iterable=itertools.chain(buffer, new_stream),
                    callbacks=[_update_chat_history]
                )
                iterator.content = content
                for token in iterator:
                    print(f"{token=}")
                    yield token
                    if ToolSymbol.TOOL_OUTPUT.value in token:  # meet a tool call end, then look back to extract
                        tool_call = ToolCall.from_string(iterator.content)
                        result = tool_call.execute()
                        prompt_value += iterator.content + result + ToolSymbol.TOOL_END.value
                        new_iterator = _stream(prompt_value,
                                               self.llm.bind(grammar=self.grammar.replace(
                                                   f'''"{self.session.npc.character_name.encode('unicode-escape').decode('utf-8')}:"''',
                                                   '', 1)),
                                               result + ToolSymbol.TOOL_END.value,
                                               iterator.content)
                        print(self.grammar.replace(
                                                   f"{self.session.npc.character_name.encode('unicode-escape').decode('utf-8')}:",
                                                   '', 1))
                        del iterator
                        yield from new_iterator
                        return

            prompt_value = prompt_template.invoke(params)
            yield from _stream(prompt_value, self.llm, '')


class CreateScenarioByChat:
    format_instructions = PydanticOutputParser(pydantic_object=Scenario).get_format_instructions()
    prompt_template = ChatPromptTemplate.from_messages([
        HumanMessage(content="""a scenario in intimacy"""),
        AIMessage(
            content="""{"scenario_name":"Beneath the Starlit Sky","scenario_description":"As the din of conflict fades into the silence of the night, {player_name} and {npc_name} find themselves sharing a serene moment beneath the vast, starlit sky. The scars of battle lay forgotten as they exchange stories of their pasts and hopes for the future. In the quiet of the night, with the gentle crackle of the campfire and the soft murmur of the forest around them, they forge a bond that transcends the chaos of their lives."}"""),
        HumanMessage(content="""the player accidentally come to the world of npc and meet the npc""")])
    player = Character(
        character_name="Human",
        persona="Need help to generate scenario.",
    )
    npc = Character(
        character_name="AI",
        persona="Creative and accurate."
    )
    scenario = Scenario(
        scenario_name="default",
        scenario_description=f"""User is asking Professional Creator to create a scenario in JSON format based on descriptions.
{format_instructions}

Examples:
{prompt_template.format()}""".replace("{", '{{').replace("}", "}}"),
    )

    @classmethod
    def create(cls, description, llm):
        session = Session(session_id="ScenarioCreation",
                          collection_name="System",
                          npc=cls.npc,
                          player=cls.player,
                          scenario=cls.scenario,
                          )
        chat = Chat(
            llm=llm,
            session=session,
            chat_prompt_template=NO_HISTORY_CHAT_PROMPT_TEMPLATE,
            grammar=json_schema_to_gbnf(json.dumps(_Scenario_v2.model_json_schema()).replace("allOf", "oneOf")),
        )
        result = chat.invoke(description)
        result = json.loads(result)
        result['meta'] = Meta_v2(**result.get('meta', {}))
        result['type'] = 'scenario'
        return Scenario(**result)


class CreateCharacterByChat:
    """
    A class that creates a character by chat.

    Attributes:
        format_instructions (str): The format instructions for the character.
        prompt_template (ChatPromptTemplate): The chat prompt template.
        player (Character): The player character.
        npc (Character): The non-player character (NPC).
        scenario (Scenario): The scenario.

    Methods:
        create(cls, description: str, llm: LlamaCpp): Creates a character by chat.
    """
    format_instructions = PydanticOutputParser(pydantic_object=Character).get_format_instructions()
    prompt_template = ChatPromptTemplate.from_messages([HumanMessage(content="""a furry character"""),
                                                        AIMessage(
                                                            content=r"""{"character_name":"Seraphina Pawsley","persona":"Seraphina Pawsley, a spirited anthropomorphic red panda, stands at the intersection of human intelligence and the agility of the wild. With a lush coat patterned with fiery hues and cream, she's a vibrant spirit who combines her innate climbing skills with a knack for mechanical invention. Her eyes, a deep emerald, gleam with curiosity and a playful wisdom. She's a master tinkerer, often seen with a tool belt and goggles, ready to leap into adventure or repair a steam-powered contraption in the bustling city of Gearford. Despite her small stature, she's a fierce ally, using her sharp wit and acrobatic prowess to navigate through the urban jungle. Her fluffy ringed tail is not only a symbol of her heritage but serves as a balance aid when she's leaping from rooftop to rooftop, chasing down the latest mystery or invention that's caught her keen eye.","meta":{"tags":["Anthropomorphic","Red Panda","Female","Inventor","Steampunk"]}}"""),
                                                        HumanMessage(content="""a sport wolf boy kid"""),
                                                        AIMessage(
                                                            content=r"""{"character_name":"Dash Howler","persona":"Dash Howler is a youthful, anthropomorphic wolf with a passion for sports and a heart full of determination. Standing at an energetic 4'5\", his sleek silver fur is accented with dynamic streaks of black that seem to mimic the swiftness of his movements. His bright, azure eyes are always focused on the goal, whether it's a soccer ball or the finish line. Dash's athletic build, a blend of natural lupine grace and the muscular development of a young athlete, gives him an edge in agility and speed. His large, expressive ears tilt and pivot with his moods, and his bushy tail wags with the enthusiasm of a pup. Always dressed in his favorite team's jersey and sport shorts, Dash is the epitome of a sports fanatic, and his paws are rarely still, tapping or dribbling an imaginary ball even when he's at rest. Despite his competitive spirit, he's known for his fair play and encouraging howls, making him a beloved teammate and an inspiring young sports icon.","meta":{"tags":["Anthropomorphic","Wolf","Male","Kid","Sports Enthusiast"]}}"""),
                                                        HumanMessage(content="""a cool human boy"""),
                                                        AIMessage(
                                                            content=r"""{"character_name":"Zane Ryder","persona":"Zane Ryder is the quintessence of cool, a teenage boy with a laid-back demeanor and a sharp sense of style. With his tousled jet-black hair and piercing ice-blue eyes, he has an effortless charm that turns heads at his high school. Standing at a casual 5'11\", Zane has a lean build honed by his love for skateboarding and urban exploration. His wardrobe is a curated collection of vintage band tees, worn-in jeans, and the latest sneakers. Accessories like his signature leather wristband and a pair of aviator sunglasses complete his look. Zane is not just about appearances; his cool factor is matched by a warm heart and a quick wit. He's the guy who always has a clever joke at the ready, but also an insightful word for friends in need. Despite his popularity, he remains approachable and down-to-earth, preferring a chill evening with close friends to big, noisy parties. Zane's coolness isn't just an act; it's a way of life, and it shows in his every confident, yet nonchalant stride.","meta":{"tags":["Human","Boy","Teenager","Skateboarder","Cool","Stylish"]}}""")])
    player = Character(
        character_name="Human",
        persona="Need help to generate character.",
    )
    npc = Character(
        character_name="AI",
        persona="Creative and accurate."
    )
    scenario = Scenario(
        scenario_name="default",
        scenario_description=f"""User is asking Professional Creator to generate a character sheet in JSON format based on descriptions.
{format_instructions}

Examples:
{prompt_template.format()}""".replace("{", '{{').replace("}", "}}"),
    )

    @classmethod
    def create(cls, description: str, llm: LlamaCpp):
        """
        Creates a character by chat.

        Args:
            description (str): The description of the character.
            llm (LlamaCpp): The LlamaCpp instance.

        Returns:
            Character: The created character.
        """
        session = Session(session_id="CharactorCreation",
                          collection_name="System",
                          npc=cls.npc,
                          player=cls.player,
                          scenario=cls.scenario,
                          )
        chat = Chat(
            llm=llm,
            session=session,
            chat_prompt_template=NO_HISTORY_CHAT_PROMPT_TEMPLATE,
            grammar=json_schema_to_gbnf(json.dumps(_Character_v2.model_json_schema()).replace("allOf", "oneOf")),
        )
        result = chat.invoke(description)
        result = json.loads(result)
        result['meta'] = Meta_v2(**result.get('meta', {}))
        result['type'] = 'character'
        return Character(**result)


class _Session_v2(BaseModel):
    """
    A Pydantic model for session data used to generate GBNF grammar.

    Attributes:
        npc (_Character_v2): The non-player character (NPC) in the session.
        player (_Character_v2): The player character in the session.
        scenario (_Scenario_v2): The scenario of the session.
    """
    npc: _Character_v2 = Field(description="Characteristics of the npc")
    player: _Character_v2 = Field(description="Characteristics of the player")
    scenario: _Scenario_v2 = Field(description="Characteristics of the scenario")


class CreateSessionByChat:
    """
    A class that creates a session by chat.

    Attributes:
        _Session (BaseModel_v1): A Pydantic model for session data.
        format_instructions (str): The format instructions for the session.
        prompt_template (ChatPromptTemplate): The chat prompt template.
        player (Character): The player character.
        npc (Character): The non-player character (NPC).
        scenario (Scenario): The scenario.
    """

    class _Session(BaseModel_v1):
        """
        A Pydantic model for session data.

        Attributes:
            npc (Character): The non-player character (NPC) in the session.
            player (Character): The player character in the session.
            scenario (Scenario): The scenario of the session.
        """
        npc: Character = Field_v1(None, description="Characteristics of the npc")
        player: Character = Field_v1(None, description="Characteristics of the player")
        scenario: Scenario = Field_v1(None, description="Characteristics of the scenario")

    format_instructions = PydanticOutputParser(pydantic_object=_Session).get_format_instructions()
    prompt_template = ChatPromptTemplate.from_messages([HumanMessage(
        content="""A time-traveling historian from the future arrives in the court of a Renaissance monarch, aiming to observe history firsthand."""),
        AIMessage(
            content=r"""{"npc":{"character_name":"Queen Isabella the Wise","persona":"Queen Isabella the Wise reigns with a sharp mind and a compassionate heart, her rule marked by a golden age of prosperity and enlightenment. Her regal bearing is softened by the warmth in her brown eyes, and her voice carries the weight of her authority yet resonates with the kindness of her spirit. Robes of rich velvet and intricate jewelry befitting her status drape her form, and her crown sits upon chestnut curls with the ease of one born to lead.","meta":{"tag":["Human","Female","Monarch","Wise","Compassionate"]},"type":"character"},"player":{"character_name":"Dr. Morgan Sinclair","persona":"Dr. Morgan Sinclair is a visionary historian from a future where time travel is a reality. With technology disguised as period attire, Morgan steps into the past with a blend of academic fervor and genuine wonder. Their appearance is unassuming, with practical clothing and a satchel full of instruments from their own time, allowing them to blend into the background and observe history as it unfolds. Their keen eye misses nothing, and their presence in the court of {npc_name} is a careful dance between observer and unwitting participant.","meta":{"tag":["Human","Non-binary","Historian","Time Traveler","Observer"]},"type":"character"},"scenario":{"scenario_name":"Echoes of the Past","scenario_description":"In the opulent halls of Queen Isabella's court, {player_name} navigates the delicate intricacies of Renaissance politics and intrigue, all while trying to maintain the facade of a humble courtier. As {player_name} documents the era for future generations, they must also ensure that their own presence does not alter the course of history they've come to study.","meta":{"tags":["Renaissance","Monarchy","Time Travel","Observation","Intrigue"]},"type":"scenario"}}"""),
        HumanMessage(
            content="""A notorious pirate captain captures a nobleman's child, unaware that the youth is an adept swordsman."""),
        AIMessage(
            content=r"""{"npc":{"character_name":"Captain Blacktide","persona":"Captain Blacktide is the feared pirate lord of the seven seas, his name synonymous with dread and his ship, the Siren's Wail, a harbinger of doom. His weathered face, marked by a jagged scar across his left eye, tells tales of countless battles. The captain's voice is a deep rumble like distant thunder, commanding and quick to anger. His attire is as dark as the ocean's depths, adorned with trinkets plundered from his conquests, and his cutlass, ever at his side, has tasted the blood of many.","meta":{"tag":["Human","Male","Pirate Captain","Notorious","Fearsome"]},"type":"character"},"player":{"character_name":"Julian Fairwind","persona":"Julian Fairwind is a youthful nobleman with a secret talent for swordsmanship, honed in the dead of night away from prying eyes. His appearance is deceivingly delicate, with finely tailored clothes and an air of aristocratic grace. However, beneath the surface lies a fierce warrior spirit and a keen intellect, both of which are masked by his disarming smile and polite demeanor. Julian's blue eyes sparkle with the thrill of adventure, and his hand is always ready on the hilt of his hidden rapier.","meta":{"tag":["Human","Male","Nobleman","Swordsman","Adventurous"]},"type":"character"},"scenario":{"scenario_name":"The Noble Captive","scenario_description":"Aboard the infamous Siren's Wail, {npc_name} revels in his latest capture, the young {player_name}, not realizing the noble's child is more than meets the eye. As the ship cuts through the waves, a game of cat and mouse ensues, with the stakes as high as the rolling seas, and secrets ready to be unsheathed like the swords at their sides.","meta":{"tags":["High Seas","Piracy","Captivity","Duel","Revelation"]},"type":"scenario"}}"""),
        HumanMessage(
            content="""A reclusive alchemist known for her potent potions inadvertently sells a transformation elixir to an unsuspecting traveler."""),
        AIMessage(
            content=r"""{"npc":{"character_name":"Selene Nightshade","persona":"Selene Nightshade is an enigmatic and solitary alchemist whose mastery over potions is unrivaled. Cloaked in robes the color of midnight, her presence is as elusive as the waning moon. Her eyes, a piercing violet, seem to hold the mysteries of the cosmos, reflecting a mind always at work. Her slender fingers are stained with the residue of magical ingredients, and her soft, hushed voice weaves through the quiet of her cluttered apothecary like a secret. Despite her reclusiveness, the allure of her potions draws a steady stream of brave souls to her door.","meta":{"tag":["Human","Female","Alchemist","Reclusive","Mysterious"]},"type":"character"},"player":{"character_name":"Rowan Thistledown","persona":"Rowan Thistledown is a carefree traveler with a heart full of wanderlust and eyes brimming with curiosity. His disheveled hair and well-worn clothes speak of many miles trekked and many lands explored. A smile is never far from his lips, and his laughter is as infectious as his enthusiasm for new experiences. Rowan's backpack, patched and frayed, carries souvenirs of his adventures, but it's his open spirit that invites the most extraordinary encounters.","meta":{"tag":["Human","Male","Traveler","Adventurous","Curious"]},"type":"character"},"scenario":{"scenario_name":"Elixir of Change","scenario_description":"In the bustling market of a medieval town, {player_name} stumbles upon the hidden shop of {npc_name}, an alchemist whose potions are whispered about in awe. When {player_name} unwittingly purchases a potion of transformation, the effects are both astonishing and unpredictable, leading to a series of misadventures that challenge the very perception of reality.","meta":{"tags":["Medieval","Magic","Transformation","Adventure","Mystery"]},"type":"scenario"}}""")])
    player = Character(
        character_name="Human",
        persona="Need help to generate character.",
    )
    npc = Character(
        character_name="AI",
        persona="Creative and accurate."
    )
    scenario = Scenario(
        scenario_name="default",
        scenario_description=f"""User is asking Professional Creator to generate a roleplay game sheet in JSON format based on descriptions.
You may refer to player and npc as {{player_name}} and {{npc_name}} in persona and scenario_description.
        
{format_instructions}

Examples:
{prompt_template.format()}""".replace("{", '{{').replace("}", "}}"),
    )

    @classmethod
    def create(cls, description, llm, session_id=None, collection_name="Session") -> Session:
        """
        Creates a session by chat.

        Args:
            description (str): The description of the character.
            llm (LlamaCpp): The LlamaCpp instance.

        Returns:
            Session: The created session.
        """
        session = Session(session_id="CharactorCreation",
                          collection_name="System",
                          npc=cls.npc,
                          player=cls.player,
                          scenario=cls.scenario,
                          )
        chat = Chat(
            llm=llm,
            session=session,
            chat_prompt_template=NO_HISTORY_CHAT_PROMPT_TEMPLATE,
            grammar=json_schema_to_gbnf(json.dumps(_Session_v2.model_json_schema()).replace("allOf", "oneOf")),
        )
        result = chat.invoke(description)
        result = json.loads(result)
        npc = Character.from_dict(result['npc'])
        player = Character.from_dict(result['player'])
        scenario = Scenario.from_dict(result['scenario'])
        return Session(
            session_id=session_id,
            npc=npc,
            player=player,
            scenario=scenario,
            collection_name=collection_name
        )


__all__ = [
    "LlamaCpp",
    "Chat",
    "Session",
    "Character",
    "Scenario"
]
