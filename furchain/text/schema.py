import json
from typing import Optional, Any, Iterable, Iterator

import requests
from langchain.output_parsers import PydanticOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import SystemMessage, messages_from_dict
from langchain_core.messages import messages_to_dict
from langchain_core.prompts import AIMessagePromptTemplate, \
    MessagesPlaceholder
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.pydantic_v1 import BaseModel as BaseModel_v1, Field as Field_v1
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.utils import Output
from llama_cpp.llama_grammar import json_schema_to_gbnf
from pydantic import BaseModel, Field
from pymongo import MongoClient

from furchain.config import TextConfig
from furchain.text.callbacks import StrChunkCallbackIterator
from furchain.text.chat_format import ChatFormat
from furchain.text.chat_message_history import MongoDBChatMessageHistory, logger
from furchain.text.chat_prompt_templates import ROLEPLAY_CHAT_PROMPT_TEMPLATE, NO_HISTORY_CHAT_PROMPT_TEMPLATE
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
    tags: list[str] = Field(default_factory=list, description="The tags of the meta data")


class Scenario_v2(BaseModel):
    scenario_name: str = Field(description="The name of the scenario")
    scenario_description: str = Field(description="The description of the scenario")
    meta: Meta_v2 = Field(default_factory=Meta_v2, description="The meta data of the scenario")
    type: str = "scenario"


class Scenario(BaseModel_v1):
    scenario_name: str = Field_v1(description="The name of the scenario")
    scenario_description: str = Field_v1(description="The description of the scenario")
    meta: dict = Field_v1(default_factory=dict, description="The meta data of the scenario")
    type: str = "scenario"

    @classmethod
    def create(cls, description: str, llm):
        return CreateLoboScenarioByChat.create(description, llm)

    @classmethod
    def from_mongo(cls, scenario_name: str, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None):

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
        return cls.from_dict(requests.get(url).json())

    @classmethod
    def from_file(cls, file_path: str):
        with open(file_path, 'r') as f:
            return cls.from_dict(json.load(f))

    def to_dict(self):
        return {
            "scenario_name": self.scenario_name,
            "scenario_description": self.scenario_description,
            "meta": self.meta
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def to_file(self, file_path: str):
        with open(file_path, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict):
        data = data.copy()

        return Scenario(
            scenario_name=data['scenario_name'],
            scenario_description=data['scenario_description'],
            meta=Meta_v2(**data['meta'])
        )


class Character_v2(BaseModel):
    character_name: str = Field(description="The name of the character")
    persona: str = Field(description="The persona of the character")
    meta: Meta_v2 = Field(default_factory=Meta_v2, description="The meta data of the character")
    type: str = "character"


class Character(BaseModel_v1):
    character_name: str = Field_v1(description="The name of the character")
    persona: str = Field_v1(description="The persona of the character")
    meta: dict = Field_v1(default_factory=dict, description="The meta data of the character")
    type: str = "character"

    @classmethod
    def create(cls, description, llm):
        return CreateLoboCharacterByChat.create(description, llm)

    @classmethod
    def from_mongo(cls, character_name: str, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None):

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
        return cls.from_dict(requests.get(url).json())

    @classmethod
    def from_file(cls, file_path: str):
        with open(file_path, 'r') as f:
            return cls.from_dict(json.load(f))

    def to_dict(self):
        return {
            "character_name": self.character_name,
            "persona": self.persona,
            "meta": self.meta,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_file(self, file_path: str):
        with open(file_path, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict):

        return Character(
            character_name=data['character_name'],
            persona=data['persona'],
            meta=data['meta'],
        )


class LlamaCpp(Runnable):
    def __init__(self, base_url=None, api_key=None, chat_format: ChatFormat = ChatFormat.ExtendedAlpaca, **kwargs):
        self.client = LlamaCppClient(base_url, api_key)
        self.chat_format = chat_format
        self.model_kwargs = kwargs

    def invoke(self, input: str | list | dict, config: Optional[RunnableConfig] = None, **kwargs) -> Output:
        if isinstance(input, (str, list)):
            input = {"prompt": input}
        return self.client.complete(input, **kwargs, **self.model_kwargs)['content']

    def stream(
            self,
            input: str | list | dict,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        if isinstance(input, (str, list)):
            input = {"prompt": input}
        for i in self.client.stream(input, **kwargs, **self.model_kwargs):
            yield i['content']


class ChatLLM:
    def __new__(cls, api,
                **kwargs) -> Runnable:
        llm = ChatOpenAI(
            openai_api_base=api,
            openai_api_key='none',
            **kwargs
        )
        return llm


class Session:

    def __init__(self, session_id: str = None,
                 npc: Character = None,
                 scenario: Scenario = None,
                 player: Character = None,
                 collection_name: str = "Session",
                 ):
        self.session_id = session_id
        self.npc = npc if npc is not None else Character(character_name=TextConfig.get_npc_name(),
                                                         persona=TextConfig.get_npc_persona())
        self.player = player if player is not None else Character(character_name=TextConfig.get_player_name(),
                                                                  persona=TextConfig.get_player_persona())
        self.scenario = scenario if scenario is not None else Scenario(scenario_name="default",
                                                                       scenario_description=TextConfig.get_scenario_description())
        self.chat_history_proxy = MongoDBChatMessageHistory(
            connection_string=TextConfig.get_mongo_url(),
            database_name=TextConfig.get_mongo_db(),
            collection_name=collection_name,
            session_id=session_id,
            npc=self.npc,
            player=self.player,
            scenario=self.scenario,
        )

    @classmethod
    def create(cls, description: str, llm: LlamaCpp):
        ...

    @property
    def messages(self):
        return self.chat_history_proxy.messages

    def add_messages(self, messages):
        return self.chat_history_proxy.add_messages(messages)

    def add_message(self, message):
        return self.chat_history_proxy.add_message(message)

    def delete(self):
        return self.chat_history_proxy.clear()


class Chat(Runnable):

    def __init__(self, llm: LlamaCpp | Runnable,
                 session: Session,
                 chat_prompt_template: ChatPromptTemplate = None,
                 response_prefix: str = '',
                 grammar: str = '',
                 **kwargs):
        super().__init__()
        chat_format = llm.chat_format
        self.kwargs = kwargs
        chat_format_parser = chat_format.parser if isinstance(chat_format, ChatFormat) else ChatFormat(
            chat_format).parser
        self.llm = llm.bind(stop=llm.model_kwargs.get("stop", []) + chat_format_parser.stop, grammar=grammar)
        self.chat_format_parser = chat_format_parser
        self.session = session
        self.response_prefix = response_prefix
        self.chat_prompt_template = chat_prompt_template if chat_prompt_template is not None else ROLEPLAY_CHAT_PROMPT_TEMPLATE

    def _get_chain_params(self, query: str, response_prefix: str = None,
                          **kwargs):
        if response_prefix is None:
            response_prefix = self.response_prefix

        chain = (
                RunnableLambda(lambda x: (
                    self.chat_prompt_template.format_prompt(chat_history=messages_from_dict(x.pop('chat_history', [])),
                                                            **x)
                ))
                | RunnableLambda(self.chat_format_parser.parse)
                | RunnableLambda(lambda x: (logger.debug("Prompt: " + x + response_prefix), x + response_prefix)[1])
                | self.llm
        )
        history_messages = self.session.messages
        for i in history_messages:
            if isinstance(i, HumanMessage):
                i.content = i.content.removeprefix(f"{self.session.player.character_name}: ")
                i.content = f"{self.session.player.character_name}: {i.content}"
            elif isinstance(i, AIMessage):
                i.content = i.content.removeprefix(f"{self.session.npc.character_name}: ")
                i.content = f"{self.session.npc.character_name}: {i.content}"
        chat_history = messages_to_dict(history_messages)
        kwargs['npc_name'] = self.session.npc.character_name
        kwargs['npc_persona'] = self.session.npc.persona
        kwargs['player_persona'] = self.session.player.persona
        kwargs['player_name'] = self.session.player.character_name
        kwargs['scenario_description'] = self.session.scenario.scenario_description.format(
            npc_name=self.session.npc.character_name,
            player_name=self.session.player.character_name)
        kwargs['query'] = query
        kwargs['chat_history'] = chat_history
        kwargs['response_prefix'] = response_prefix

        def _update_chat_history(response_with_prefix):
            human_message = HumanMessage(content=f"{query}")
            ai_message = AIMessage(content=f"{response_with_prefix}")
            self.session.add_messages([
                human_message,
                ai_message
            ])

        return chain, kwargs, _update_chat_history

    def invoke(
            self, input: dict | str, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> Output:
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
        params = {}
        if isinstance(input, str):
            input = {'query': input}
        params.update(input)
        params.update(kwargs)
        chain, params, _update_chat_history = self._get_chain_params(**params)
        stream = chain.stream(params, config)
        logger.debug(f"stream input: {params}")
        yield from StrChunkCallbackIterator(
            iterable=stream,
            callbacks=[_update_chat_history],
            response_prefix=params['response_prefix'],
        )


class CreateLoboScenarioByChat:
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

Pay attention special tokens: {{player_name}}, {{npc_name}}.

Examples:
{prompt_template.format()}""".replace("{", '{{').replace("}", "}}"),
    )

    class Scenario(BaseModel):
        scenario_name: str = Field(description="The name of the scenario")
        scenario_description: str = Field(description="The description of the scenario")
        meta: Meta_v2 = Field(default_factory=Meta_v2, description="The meta data of the scenario")
        type: str = "scenario"


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
            grammar=json_schema_to_gbnf(json.dumps(cls.Scenario.model_json_schema())),
            response_prefix=''
        )
        result = chat.invoke(description)
        result = json.loads(result)
        result['meta'] = Meta_v2(**result.get('meta', {}))
        result['type'] = 'scenario'
        return Scenario(**result)


class CreateLoboCharacterByChat:
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
        persona="Need help to generate charactor.",
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
    def create(cls, description, llm):
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
            grammar=json_schema_to_gbnf(json.dumps(Character_v2.model_json_schema())),
            response_prefix=''
        )
        result = chat.invoke(description)
        result = json.loads(result)
        result['meta'] = Meta_v2(**result.get('meta', {}))
        result['type'] = 'character'
        return Character(**result)

