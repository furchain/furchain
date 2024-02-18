import json
import uuid
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
from furchain.text.chat_prompt_templates import ROLEPLAY_CHAT_PROMPT_TEMPLATE, NORMAL_CHAT_PROMPT_TEMPLATE
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
    example_chat_history_template: ChatPromptTemplate = Field(
        default_factory=lambda: ChatPromptTemplate.from_messages(list()),
        description="The example chat history template")
    meta: Meta_v2 = Field(default_factory=Meta_v2, description="The meta data of the scenario")
    type: str = "scenario"


class Scenario(BaseModel_v1):
    scenario_name: str = Field_v1(description="The name of the scenario")
    scenario_description: str = Field_v1(description="The description of the scenario")
    example_chat_history_template: ChatPromptTemplate = Field_v1(
        default_factory=lambda: ChatPromptTemplate.from_messages(list()),
        description="The example chat history template")
    meta: dict = Field_v1(default_factory=dict, description="The meta data of the scenario")
    type: str = "scenario"

    @classmethod
    def create(cls, description: str, llm, chat_format=ChatFormat.ExtendedAlpaca):
        return CreateLoboScenarioByChat.create(description, llm, chat_format)

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
                     "example_chat_history_template": document["example_chat_history_template"],
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
        example_chat_history_template = []
        for message in self.example_chat_history_template.messages:
            example_chat_history_template.append({
                **message.dict(),
                'type': message.__class__.__name__,
            })

        return {
            "scenario_name": self.scenario_name,
            "scenario_description": self.scenario_description,
            "example_chat_history_template": {'messages': example_chat_history_template},
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
        example_chat_history_template = []
        for message in data['example_chat_history_template']['messages']:
            message_type = message.pop('type')
            if message_type in CLASS_DICT:
                message_class = CLASS_DICT[message_type]
            else:
                message_class = globals()[message_type]  # try to get the class from the global namespace
            if 'PromptTemplate' in message_type:

                example_chat_history_template.append(
                    message_class.from_template(**message['prompt'])
                )
            else:
                example_chat_history_template.append(
                    message_class(**message)
                )

        return Scenario(
            scenario_name=data['scenario_name'],
            scenario_description=data['scenario_description'],
            example_chat_history_template=ChatPromptTemplate(messages=example_chat_history_template),
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
    def create(cls, description, llm, chat_format=ChatFormat.ExtendedAlpaca):
        return CreateLoboCharacterByChat.create(description, llm, chat_format)

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
    def __init__(self, base_url=None, api_key=None, **kwargs):
        self.client = LlamaCppClient(base_url, api_key)
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

class Chat(Runnable):

    def __init__(self, llm: LlamaCpp | Runnable, chat_format: str | ChatFormat = None,
                 chat_prompt_template: ChatPromptTemplate = None,
                 npc: Character_v2 = None,
                 scenario: Scenario_v2 = None,
                 player: Character_v2 = None,
                 session_id: str = None,
                 response_prefix: str = '',
                 grammar: str = '',
                 **kwargs):
        super().__init__()
        if chat_format is None:
            chat_format = ChatFormat.ExtendedAlpaca
        self.chat_format = chat_format
        self.kwargs = kwargs
        self.npc = npc if npc is not None else Character_v2(character_name=TextConfig.get_npc_name(),
                                                            persona=TextConfig.get_npc_persona())
        #
        # if grammar:
        #     extra_body = llm.model_kwargs.get('extra_body', {})
        #     extra_body['grammar'] = grammar
        #     llm.model_kwargs['extra_body'] = extra_body
        # chat_format_parser = chat_format.parser if isinstance(chat_format, ChatFormat) else ChatFormat(
        #     chat_format).parser
        # llm.model_kwargs.update(kwargs.get("model_kwargs", {}))
        # stop = llm.model_kwargs['extra_query'].get('stop', []) + chat_format_parser.stop
        chat_format_parser = chat_format.parser if isinstance(chat_format, ChatFormat) else ChatFormat(
            chat_format).parser
        self.llm = llm.bind(stop=llm.model_kwargs.get("stop", []) + chat_format_parser.stop, grammar=grammar)
        self.chat_format_parser = chat_format_parser
        self.player = player if player is not None else Character_v2(character_name=TextConfig.get_player_name(),
                                                                     persona=TextConfig.get_player_persona())
        self.scenario = scenario if scenario is not None else Scenario_v2(scenario_name="default",
                                                                          scenario_description=TextConfig.get_scenario_description())
        self.session_id = session_id if session_id is not None else uuid.uuid4().__str__()
        self.response_prefix = response_prefix
        self.chat_prompt_template = chat_prompt_template if chat_prompt_template is not None else ROLEPLAY_CHAT_PROMPT_TEMPLATE


    def create_room(self, initial_message: str):
        scenario = self.scenario.copy()
        if scenario.example_chat_history_template.messages:
            scenario.example_chat_history_template.messages.pop()
        agent = Chat(
            llm=self.llm,
            chat_format=self.chat_format,
            npc=self.player,
            player=self.npc,
            session_id=(self.session_id + '_agent') if self.session_id else None,
            scenario=scenario,
            **self.kwargs
        )
        player_message = initial_message

        def _run():
            nonlocal player_message
            while True:
                chat = self.stream(player_message)
                npc_message = ''
                for i in chat:
                    npc_message += i
                    yield i
                yield None
                chat = agent.stream(npc_message.lstrip(agent.player.character_name + ': '))
                player_message = ''
                for i in chat:
                    player_message += i
                    yield i
                yield None

        yield from _run()

    def get_example_chat_history(self):
        return self.scenario.example_chat_history_template.format_messages(
            npc_name=self.npc.character_name,
            npc_persona=self.npc.persona,
            player_persona=self.player.persona,
            player_name=self.player.character_name,
            scenario_description=self.scenario.scenario_description,
        )

    def _get_chain_params(self, query: str,
                          session_id: str = None, response_prefix: str = None,
                          **kwargs):
        if response_prefix is None:
            response_prefix = self.response_prefix
        if session_id is None:
            session_id = self.session_id

        chain = (
                RunnableLambda(lambda x: (
                    self.chat_prompt_template.format_prompt(chat_history=messages_from_dict(x.pop('chat_history', [])),
                                                            **x)
                ))
                | RunnableLambda(self.chat_format_parser.parse)
                | RunnableLambda(lambda x: (logger.debug("Prompt: " + x + response_prefix), x + response_prefix)[1])
                | self.llm
        )
        chat_history_proxy = MongoDBChatMessageHistory(
            connection_string=TextConfig.get_mongo_url(),
            database_name=TextConfig.get_mongo_db(),
            collection_name=self.npc.character_name,
            session_id=session_id,
            npc_name=self.npc.character_name,
            player_name=self.player.character_name,
            scenario_name=self.scenario.scenario_name,
        )
        history_messages = chat_history_proxy.messages
        for i in history_messages:
            if isinstance(i, HumanMessage):
                i.content = i.content.removeprefix(f"{self.player.character_name}: ")
                i.content = f"{self.player.character_name}: {i.content}"
            elif isinstance(i, AIMessage):
                i.content = i.content.removeprefix(f"{self.npc.character_name}: ")
                i.content = f"{self.npc.character_name}: {i.content}"
        chat_history = messages_to_dict(history_messages)
        kwargs['npc_name'] = self.npc.character_name
        kwargs['npc_persona'] = self.npc.persona
        kwargs['player_persona'] = self.player.persona
        kwargs['player_name'] = self.player.character_name
        kwargs['scenario_description'] = self.scenario.scenario_description.format(npc_name=self.npc.character_name,
                                                                                   player_name=self.player.character_name)
        kwargs['query'] = query
        kwargs['chat_history'] = chat_history
        kwargs['response_prefix'] = response_prefix
        kwargs['example_chat_history'] = self.scenario.example_chat_history_template.format_messages(**kwargs)

        def _update_chat_history(response_with_prefix):
            human_message = HumanMessage(content=f"{query}")
            ai_message = AIMessage(content=f"{response_with_prefix}")
            chat_history_proxy.add_messages([
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
        yield ''


class CreateLoboScenarioByChat:
    format_instructions = PydanticOutputParser(pydantic_object=Scenario).get_format_instructions()
    prompt_template = ChatPromptTemplate.from_messages([
        HumanMessage(content="""a scenario in intimacy"""),
        AIMessage(
            content="""{"scenario_name":"Beneath the Starlit Sky","scenario_description":"As the din of conflict fades into the silence of the night, {player_name} and {npc_name} find themselves sharing a serene moment beneath the vast, starlit sky. The scars of battle lay forgotten as they exchange stories of their pasts and hopes for the future. In the quiet of the night, with the gentle crackle of the campfire and the soft murmur of the forest around them, they forge a bond that transcends the chaos of their lives."}"""),
        HumanMessage(content="""the player accidentally come to the world of npc and meet the npc""")])
    player = Character(
        character_name="User",
        persona="Need help.",
    )
    npc = Character(
        character_name="Professional Creator",
        persona="Creative and accurate."
    )
    scenario = Scenario(
        scenario_name="default",
        scenario_description=f"""User is asking Professional Creator to create a scenario in JSON format based on descriptions.
{format_instructions}
**Note:**
- Choose a suitable name for the scenario based on the description
- Example chat history should fit the scenario
- Use `player_name` and `npc_name` as placeholders""".replace("{", '{{').replace("}", "}}"),
        example_chat_history_template=prompt_template
    )

    class Scenario(BaseModel):
        scenario_name: str = Field(description="The name of the scenario")
        scenario_description: str = Field(description="The description of the scenario")
        meta: Meta_v2 = Field(default_factory=Meta_v2, description="The meta data of the scenario")
        type: str = "scenario"


    @classmethod
    def create(cls, description, llm, chat_format=ChatFormat.ExtendedAlpaca):
        chat = Chat(
            llm=llm,
            chat_format=chat_format,
            npc=cls.npc,
            player=cls.player,
            scenario=cls.scenario,
            chat_prompt_template=NORMAL_CHAT_PROMPT_TEMPLATE,
            grammar=json_schema_to_gbnf(json.dumps(cls.Scenario.model_json_schema())),
            response_prefix=''
        )
        result = chat.invoke(description)
        result = json.loads(result)
        result['meta'] = Meta_v2(**result.get('meta', {}))
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
    # prompt_template = ChatPromptTemplate.from_messages([HumanMessage(content="""a furry character"""),
    #                                                    AIMessage(
    #                                                        content="""{"character_name":"Seraphina Pawsley","persona":"Seraphina Pawsley, a spirited anthropomorphic red panda, stands at the intersection of human intelligence and the agility of the wild. With a lush coat patterned with fiery hues and cream, she's a vibrant spirit who combines her innate climbing skills with a knack for mechanical invention. Her eyes, a deep emerald, gleam with curiosity and a playful wisdom. She's a master tinkerer, often seen with a tool belt and goggles, ready to leap into adventure or repair a steam-powered contraption in the bustling city of Gearford. Despite her small stature, she's a fierce ally, using her sharp wit and acrobatic prowess to navigate through the urban jungle. Her fluffy ringed tail is not only a symbol of her heritage but serves as a balance aid when she's leaping from rooftop to rooftop, chasing down the latest mystery or invention that's caught her keen eye."}""")])
    player = Character(
        character_name="User",
        persona="Need help.",
    )
    npc = Character(
        character_name="Professional Creator",
        persona="Creative and accurate."
    )
    scenario = Scenario(
        scenario_name="default",
        scenario_description=f"""User is asking Professional Creator to generate a character sheet in JSON format based on descriptions.
{format_instructions}""".replace("{", '{{').replace("}", "}}"),
        example_chat_history_template=prompt_template
    )


    @classmethod
    def create(cls, description, llm, chat_format=ChatFormat.ExtendedAlpaca):
        chat = Chat(
            llm=llm,
            chat_format=chat_format,
            npc=cls.npc,
            player=cls.player,
            scenario=cls.scenario,
            chat_prompt_template=NORMAL_CHAT_PROMPT_TEMPLATE,
            grammar=json_schema_to_gbnf(json.dumps(Character_v2.model_json_schema())),
            response_prefix=''
        )
        result = chat.invoke(description)
        result = json.loads(result)
        result['meta'] = Meta_v2(**result.get('meta', {}))

        return Character(**result)

