import json
import uuid
from typing import Optional, Any, Iterable

import requests
from langchain.output_parsers import PydanticOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms.openai import OpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import SystemMessage, messages_from_dict
from langchain_core.messages import messages_to_dict
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import AIMessagePromptTemplate, \
    MessagesPlaceholder
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.runnables.utils import Output
from llama_cpp.llama_grammar import json_schema_to_gbnf
from pymongo import MongoClient

from furchain.config import TextConfig
from furchain.text.callbacks import StrChunkCallbackIterator
from furchain.text.chat_format import ChatFormat
from furchain.text.chat_message_history import MongoDBChatMessageHistory, logger
from furchain.text.chat_prompt_templates import ROLEPLAY_CHAT_PROMPT_TEMPLATE, NORMAL_CHAT_PROMPT_TEMPLATE

CLASS_DICT = {
    'HumanMessagePromptTemplate': HumanMessagePromptTemplate,
    'AIMessagePromptTemplate': AIMessagePromptTemplate,
    'SystemMessagePromptTemplate': SystemMessagePromptTemplate,
    'HumanMessage': HumanMessage,
    'AIMessage': AIMessage,
    'SystemMessage': SystemMessage,
    'MessagesPlaceholder': MessagesPlaceholder
}


class Scenario(BaseModel):
    scenario_name: str = Field(description="The name of the scenario")
    scenario_description: str = Field(description="The description of the scenario")
    example_chat_history_template: ChatPromptTemplate = Field(
        default_factory=lambda: ChatPromptTemplate.from_messages(list()),
        description="The example chat history template")
    meta: dict = Field(default_factory=dict, description="The meta data of the scenario")
    type: str = "scenario"

    @classmethod
    def from_openai(cls, description: str):
        return CreateLoboScenarioByOpenAI.chain.invoke(description)

    @classmethod
    def from_chat(cls, description: str, api=None, chat_format=ChatFormat.ExtendedAlpaca):
        return CreateLoboScenarioByChat.create(description, api, chat_format)

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

    def save_to_mongo(self, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None):
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
            meta=data['meta']
        )


class Character(BaseModel):
    character_name: str = Field(description="The name of the character")
    persona: str = Field(description="The persona of the character")
    meta: dict = Field(default_factory=dict, description="The meta data of the character")
    type: str = "character"

    @classmethod
    def from_openai(cls, description):
        return CreateLoboCharacterByOpenAI.chain.invoke(description)

    @classmethod
    def from_chat(cls, description, api=None, chat_format=ChatFormat.ExtendedAlpaca):
        return CreateLoboCharacterByChat.create(description, api, chat_format)

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

    def save_to_mongo(self, mongo_url: str = None, mongo_db: str = None, mongo_collection: str = None):
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

    @classmethod
    def from_dict(cls, data: dict):

        return Character(
            character_name=data['character_name'],
            persona=data['persona'],
            meta=data['meta'],
        )


class LLM:
    def __new__(cls, api, chat_format: str | ChatFormat = ChatFormat.ExtendedAlpaca,
                **kwargs) -> Runnable:
        if isinstance(chat_format, ChatFormat):
            chat_format = chat_format.value
        model_kwargs = kwargs.pop("model_kwargs", {})
        extra_query = model_kwargs.get("extra_query", {})
        extra_query["chat_format"] = chat_format
        model_kwargs["extra_query"] = extra_query
        llm = OpenAI(
            openai_api_base=api,
            openai_api_key='none',
            model_kwargs=model_kwargs,
            **kwargs
        )
        return llm


class ChatLLM:
    def __new__(cls, api,
                **kwargs) -> Runnable:
        llm = ChatOpenAI(
            openai_api_base=api,
            openai_api_key='none',
            **kwargs
        )
        return llm


class CreateLoboCharacterByOpenAI:
    llm = ChatOpenAI(model_name='gpt-3.5-turbo-1106')
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template("""Create a character sheet in JSON object based on given description. 

{format_instructions}"""), HumanMessage(content="""a furry character"""),
        AIMessage(
            content="""{"character_name":"Seraphina Pawsley","persona":"Seraphina Pawsley, a spirited anthropomorphic red panda, stands at the intersection of human intelligence and the agility of the wild. With a lush coat patterned with fiery hues and cream, she's a vibrant spirit who combines her innate climbing skills with a knack for mechanical invention. Her eyes, a deep emerald, gleam with curiosity and a playful wisdom. She's a master tinkerer, often seen with a tool belt and goggles, ready to leap into adventure or repair a steam-powered contraption in the bustling city of Gearford. Despite her small stature, she's a fierce ally, using her sharp wit and acrobatic prowess to navigate through the urban jungle. Her fluffy ringed tail is not only a symbol of her heritage but serves as a balance aid when she's leaping from rooftop to rooftop, chasing down the latest mystery or invention that's caught her keen eye.","meta":{"tag":["Anthropomorphic","Red Panda","Female","Inventor","Steampunk"]}}"""),
        HumanMessage(content="""a sport wolf boy kid"""),
        AIMessage(
            content="""{"character_name":"Dash Howler","persona":"Dash Howler is a youthful, anthropomorphic wolf with a passion for sports and a heart full of determination. Standing at an energetic 4'5\", his sleek silver fur is accented with dynamic streaks of black that seem to mimic the swiftness of his movements. His bright, azure eyes are always focused on the goal, whether it's a soccer ball or the finish line. Dash's athletic build, a blend of natural lupine grace and the muscular development of a young athlete, gives him an edge in agility and speed. His large, expressive ears tilt and pivot with his moods, and his bushy tail wags with the enthusiasm of a pup. Always dressed in his favorite team's jersey and sport shorts, Dash is the epitome of a sports fanatic, and his paws are rarely still, tapping or dribbling an imaginary ball even when he's at rest. Despite his competitive spirit, he's known for his fair play and encouraging howls, making him a beloved teammate and an inspiring young sports icon.","meta":{"tag":["Anthropomorphic","Wolf","Male","Kid","Sports Enthusiast"]}}"""),
        HumanMessage(content="""a cool human boy"""),
        AIMessage(
            content="""{"character_name":"Zane Ryder","persona":"Zane Ryder is the quintessence of cool, a teenage boy with a laid-back demeanor and a sharp sense of style. With his tousled jet-black hair and piercing ice-blue eyes, he has an effortless charm that turns heads at his high school. Standing at a casual 5'11\", Zane has a lean build honed by his love for skateboarding and urban exploration. His wardrobe is a curated collection of vintage band tees, worn-in jeans, and the latest sneakers. Accessories like his signature leather wristband and a pair of aviator sunglasses complete his look. Zane is not just about appearances; his cool factor is matched by a warm heart and a quick wit. He's the guy who always has a clever joke at the ready, but also an insightful word for friends in need. Despite his popularity, he remains approachable and down-to-earth, preferring a chill evening with close friends to big, noisy parties. Zane's coolness isn't just an act; it's a way of life, and it shows in his every confident, yet nonchalant stride.","meta":{"tag":["Human","Boy","Teenager","Skateboarder","Cool","Stylish"]}}"""),
        HumanMessagePromptTemplate.from_template("""{description}"""),
    ]).partial(format_instructions=PydanticOutputParser(pydantic_object=Character).get_format_instructions())
    chain = (
            {"description": RunnablePassthrough()}
            | prompt_template
            | llm.bind(response_format={"type": "json_object"})
            | StrOutputParser()
            | RunnableLambda(lambda x: Character.from_dict(json.loads(x)))
    )


class CreateLoboScenarioByOpenAI:
    llm = ChatOpenAI(model_name='gpt-3.5-turbo-1106')
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template("""Create a scenario in JSON object based on given description.
{format_instructions}

**Note:**
- Choose a suitable name for the scenario based on the description
- Example chat history should fit the scenario
- `input_variables` only accepts `npc_name` and `player_name`"""),
        HumanMessage(content="""a scenario in intimacy"""),
        AIMessage(
            content="""{"scenario_name":"Beneath the Starlit Sky","scenario_description":"As the din of conflict fades into the silence of the night, {player_name} and {npc_name} find themselves sharing a serene moment beneath the vast, starlit sky. The scars of battle lay forgotten as they exchange stories of their pasts and hopes for the future. In the quiet of the night, with the gentle crackle of the campfire and the soft murmur of the forest around them, they forge a bond that transcends the chaos of their lives.","example_chat_history_template":{"messages":[{"prompt":{"input_variables":["player_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{player_name}: *Leaning back against a gnarled tree trunk, {player_name} looks up at the blanket of stars overhead, a tapestry of celestial stories twinkling in the inky expanse. The fire crackles and pops, casting a dance of shadows and light upon their face.*\n\nThe world is so vast, so full of wonder and mystery. We spend our days rushing from one battle to the next, one crisis to another, but moments like these... they make me pause. They remind me that there's beauty in stillness, in just... being.\n\n*{player_name} draws a deep breath, the cool night air filling their lungs, bringing with it the scent of pine and earth. With a thoughtful look in their eyes, they turn to {npc_name}, a soft smile gracing their lips.*\nIt's easy to lose oneself in the fight, to forget why we're fighting in the first place. But then I look at the stars, and I remember. We're fighting for moments like this, aren't we? For peace, for a chance to live—not just survive.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"HumanMessagePromptTemplate"},{"prompt":{"input_variables":["npc_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{npc_name}: *{npc_name} shifts closer to the fire, their eyes reflecting the flickering flames as they follow {player_name}'s gaze to the heavens. A thoughtful expression plays across their features, and they nod slowly in agreement.*\n\nYou speak truly, {player_name}. The stars have watched over countless souls before us, silent guardians of our histories and secrets. In their light, I find a connection to something greater than myself, a sense of timelessness that puts our struggles into perspective.\n\n*They pick up a small twig and idly poke at the embers, sending a cascade of sparks spiraling into the night. A wistful sigh escapes them as they continue.*\nThere's a story in my family, passed down through generations. It speaks of a hero who, much like us, sought solace in the night sky. They believed each star was the soul of a fallen warrior, guiding and protecting us from the beyond. I like to think there's some truth to that tale. Perhaps in this vastness, we are not alone after all.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"AIMessagePromptTemplate"},{"prompt":{"input_variables":["player_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{player_name}: *{player_name} listens intently to the story, a sense of wonder slowly washing over them. The fire's warmth spreads through their body, a stark contrast to the coolness of the night.*\n\nThat's a beautiful story, {npc_name}. It makes me think about the legacies we leave behind, the marks we make upon the world. We fight, we love, we dream, and we hope... and maybe, just maybe, that's enough to turn us into stars ourselves when our time comes.\n\n*{player_name} picks up a small stone, turning it over in their hands, feeling its weight and texture. They look back at {npc_name}, their eyes shining with a mixture of melancholy and resolve.*\nWe each carry our own scars, our own stories written in the constellations of our hearts. And tonight, we share those stories with the stars as witnesses, crafting a new chapter together. No matter where our journey takes us, this moment, this connection—it's eternal, like the stars.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"HumanMessagePromptTemplate"},{"prompt":{"input_variables":["npc_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{npc_name}: *With a gentle smile, {npc_name} reaches out to toss the twig into the fire, watching as it's consumed by the hungry flames. They turn to {player_name}, their expression soft and earnest.*\n\nYes, {player_name}, like the stars, our stories will linger long after we're gone. It's a comforting thought, isn't it? That our struggles, our joys, and our bonds might inspire others, just as the stars inspire us now.\n\n*{npc_name} stretches out their hands to the fire, seeking its warmth. They seem to gather their thoughts before speaking again, their voice barely above a whisper.*\nI've often felt alone, even in the company of others. But with you, it's different. There's a harmony, a sense of belonging. I believe that's rare and worth more than all the treasures of this world. Together, we are like two stars sharing the same sky, distinct yet connected by an invisible thread.\n\n*They lean back, looking up once more, a peaceful silence enveloping them as they sit with {player_name}, two souls intertwined in the quiet of the night.*","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"AIMessagePromptTemplate"}]},"meta":{"tags":["Intimacy","Companionship","Reflection","Peace"]},"type":"scenario"}"""),
        HumanMessage(content="""the player accidentally come to the world of npc and meet the npc"""),
        AIMessage(
            content="""{"scenario_name":"Stranger in a Strange Land","scenario_description":"In a twist of fate, {player_name} finds themselves transported to an unfamiliar world, a realm where magic weaves through the very fabric of reality and ancient prophecies speak of a stranger from another land. In this world, {player_name} encounters {npc_name}, a denizen of this strange place who is both intrigued and wary of this unexpected visitor. As they journey together, the two share profound moments beneath the canopies of whispering forests and the ruins of civilizations long past, seeking to understand the purpose behind {player_name}'s mysterious arrival.","example_chat_history_template":{"messages":[{"prompt":{"input_variables":["player_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{player_name}: *Stumbling through the dense underbrush, {player_name} emerges into a clearing, their eyes wide with a mix of confusion and awe. The sky above swirls with colors they've never seen, and the air hums with an unseen energy.*\n\nWhere... where am I? This world, it's like nothing I've ever seen. The trees speak in hushed tones, and the stars... they're all wrong. I remember the portal, the pull of something beyond my understanding, and now I'm here. But why?\n\n*{player_name} sits down on a moss-covered rock, trying to collect their thoughts. They pull out a small, worn photograph from their pocket, gazing at it with a sense of longing and resolve.*\nI don't know what force brought me here, or what it wants from me. But I have to believe there's a reason. There's always a reason. And until I find my way back... I need to survive in this beautiful, bewildering place.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"HumanMessagePromptTemplate"},{"prompt":{"input_variables":["npc_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{npc_name}: *{npc_name} watches from the shadows, curiosity piqued by the stranger's sudden appearance. They step forward, their movements as silent as the night, their presence barely felt.*\n\nYou are far from your home, {player_name}. This is the land of Eldoria, a place where the veil between worlds is thin. Your arrival was foretold in the Chronicles of the Ancients. A stranger with the power to change the tide of destiny. Could it be you?\n\n*{npc_name} extends a hand to help {player_name} to their feet, offering a tentative smile. Their eyes hold a wisdom as deep as the starlit sky above.*\nYou need not bear the weight of this new world alone, {player_name}. I will guide you, teach you our ways. Together, we will unravel the mystery of your coming. Be at ease, for you are not without allies here.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"AIMessagePromptTemplate"},{"prompt":{"input_variables":["player_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{player_name}: *Accepting {npc_name}'s hand, {player_name} rises, their eyes locking with those of their newfound companion. There's a strength in {npc_name}'s grip, a reassurance that eases the tightness in {player_name}'s chest.*\n\nForetold? I'm just an ordinary person. I don't know about destiny or chronicles, but I do know that I'm grateful for your help. This place, Eldoria, it's both terrifying and incredible. I can feel the magic in the air, a song that stirs the soul.\n\n*{player_name} takes a deep breath, looking around at the vibrant flora and fauna of Eldoria with newfound appreciation. They turn back to {npc_name}, a determined glint in their eye.*\nI may not understand why I'm here, but I won't waste this chance. You say I could change destiny? Then let's see where this path leads. Teach me, {npc_name}, and I will learn. I will do whatever it takes to find my purpose in this world.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"HumanMessagePromptTemplate"},{"prompt":{"input_variables":["npc_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{npc_name}: *Nodding solemnly, {npc_name} releases {player_name}'s hand and gestures to the forest around them.*\n\nThen learn you shall, {player_name}. Eldoria is a world of balance, of light and shadow. You must walk with care, for every step is watched by friend and foe alike. The land itself will test you, challenge you to rise above what you once were.\n\n*They lead {player_name} along a hidden path, pointing out the subtle signs of the forest's language, teaching them how to listen to the whispers of the wind and the stories of the stones.*\nAs we journey together, you will come to know the heartbeat of Eldoria. And in time, you will find your place within its rhythm. Trust in yourself, trust in the journey. The path to understanding is long, but it is walked one step at a time.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"AIMessagePromptTemplate"}]},"meta":{"tags":["Fantasy","Adventure","Mystery","Self-Discovery","Magic"]},"type":"scenario"}"""),
        HumanMessage(
            content="""the npc accidentally break into the normal life of player, and hint a start of relationship"""),
        AIMessage(
            content="""{"scenario_name":"A Twist of Worlds","scenario_description":"In an ordinary world where {player_name} leads a routine life, the unexpected happens. A rift between realms opens, and {npc_name}, a being from a place where magic is as common as the air they breathe, stumbles into {player_name}'s life. This accidental meeting disrupts the mundane, hinting at the start of something more as two vastly different lives intertwine. As they navigate this unforeseen closeness, the boundaries between ordinary and extraordinary begin to blur, and the seeds of a deeper connection are sown.","example_chat_history_template":{"messages":[{"prompt":{"input_variables":["player_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{player_name}: *{player_name} is in the midst of a typical day, the kind where every action is a repeat of the day before. As they pour a cup of coffee, the air shimmers unexpectedly in their apartment, and with a flash of light and a pop of displaced air, {npc_name} appears.*\n\nWhat in the world...? How did you get into my apartment? Who are you? This has got to be the strangest break-in ever. Are you alright? You look as confused as I feel.\n\n*{player_name} sets the coffee down, their routine forgotten. They approach {npc_name} cautiously, noting the strange attire and the bewildered look on their face.*\nYou're not from around here, are you? I mean, not just from another city, but... from somewhere else entirely. This is going to sound crazy, but do you come from another world or something?","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"HumanMessagePromptTemplate"},{"prompt":{"input_variables":["npc_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{npc_name}: *{npc_name} looks around in a daze, their eyes wide with a mix of fear and curiosity. They take in their surroundings, so different from the world they know.*\n\nI... I did not intend to intrude. My name is {npc_name}, and I am indeed from another place. A spell went awry, and I find myself here, in your world. It's much less... vibrant than my own. And I sense no magic here, only a strange, orderly calm.\n\n*{npc_name} stands up, brushing off their clothes. They give {player_name} a sheepish look, an apology written in their eyes.*\nI am at a loss, and it seems I have disrupted your day. I am not familiar with your customs, but I wish to make amends. Perhaps, in doing so, we might find some common ground, despite the vastness that separates our origins.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"AIMessagePromptTemplate"},{"prompt":{"input_variables":["player_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{player_name}: *A laugh escapes {player_name} despite the absurdity of the situation. They extend a hand to {npc_name} in a gesture of peace and hospitality.*\n\nWell, {npc_name}, you've certainly made this day interesting. And as for customs, I think the first order of business is to get you some clothes that won't draw stares. We can figure out the rest as we go along.\n\n*{player_name} begins to gather some of their own clothes that might fit {npc_name}, their mind racing with a thousand questions. Yet, there's an unspoken excitement about the unexpected.*\nYou know, I always hoped there was more to life than the daily grind. I guess I should be careful what I wish for. Let's just start with the basics and see where this goes. Who knows? This could be the beginning of a great story—or at least a very interesting friendship.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"HumanMessagePromptTemplate"},{"prompt":{"input_variables":["npc_name"],"input_types":{},"output_parser":null,"partial_variables":{},"template":"{npc_name}: *Taking the offered clothes with a nod of gratitude, {npc_name} manages a small, grateful smile.*\n\nThank you, {player_name}. Your world is already proving to be full of surprises. I am unsure what brought me here, but perhaps it was not without purpose. You speak of stories and friendship, concepts that are universal, it seems.\n\n*As {npc_name} changes into the more 'appropriate' attire, they look less like an intruder from another realm and more like someone who might just belong. They turn to {player_name}, a spark of adventure in their eyes.*\nI am in your debt, and in return, I offer my knowledge, my assistance, and perhaps, in time, my loyalty. This accident may have been the fates weaving our threads together. I am ready to see where this tapestry of chance will lead us.","template_format":"f-string","validate_template":false,"_type":"prompt"},"additional_kwargs":{},"type":"AIMessagePromptTemplate"}]},"meta":{"tags":["Urban Fantasy","Crossover","Adventure","Friendship","Romance"]},"type":"scenario"}"""),
        HumanMessagePromptTemplate.from_template("""{description}""")
    ]).partial(format_instructions=PydanticOutputParser(pydantic_object=Scenario).get_format_instructions())
    chain = (
            {"description": RunnablePassthrough()}
            | prompt_template
            | llm.bind(response_format={"type": "json_object"})
            | StrOutputParser()
            | RunnableLambda(lambda x: Scenario.from_dict(json.loads(x)))
    )


class Chat(Runnable):

    def __init__(self, api: str = None, chat_format: str | ChatFormat = None,
                 chat_prompt_template: ChatPromptTemplate = None,
                 npc: Character = None,
                 scenario: Scenario = None,
                 player: Character = None,
                 session_id: str = None,
                 response_prefix: str = '',
                 grammar: str = None,
                 **kwargs):
        super().__init__()
        if chat_format is None:
            chat_format = ChatFormat.ExtendedAlpaca
        self.chat_format = chat_format
        self.api = api
        self.kwargs = kwargs
        self.npc = npc if npc is not None else Character(character_name=TextConfig.get_npc_name(),
                                                         persona=TextConfig.get_npc_persona())

        llm: OpenAI = LLM(api=api if api is not None else TextConfig.get_llm_api(), chat_format=chat_format, **kwargs)
        if grammar:
            extra_body = llm.model_kwargs.get('extra_body', {})
            extra_body['grammar'] = grammar
            llm.model_kwargs['extra_body'] = extra_body
        chat_format_parser = chat_format.parser if isinstance(chat_format, ChatFormat) else ChatFormat(
            chat_format).parser
        llm.model_kwargs.update(kwargs.get("model_kwargs", {}))
        stop = llm.model_kwargs['extra_query'].get('stop', []) + chat_format_parser.stop

        self.llm = llm.bind(stop=stop)
        self.chat_format_parser = chat_format_parser
        self.player = player if player is not None else Character(character_name=TextConfig.get_player_name(),
                                                                  persona=TextConfig.get_player_persona())
        self.scenario = scenario if scenario is not None else Scenario(scenario_name="default",
                                                                       scenario_description=TextConfig.get_scenario_description())
        self.session_id = session_id if session_id is not None else uuid.uuid4().__str__()
        self.response_prefix = response_prefix
        self.chat_prompt_template = chat_prompt_template if chat_prompt_template is not None else ROLEPLAY_CHAT_PROMPT_TEMPLATE
        self.grammar = grammar


    def create_room(self, initial_message: str):
        scenario = self.scenario.copy()
        if scenario.example_chat_history_template.messages:
            scenario.example_chat_history_template.messages.pop()
        agent = Chat(
            api=self.api,
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
- `input_variables` only accepts `npc_name` and `player_name`""".replace("{", '{{').replace("}", "}}"),
        example_chat_history_template=prompt_template
    )

    class _Scenario(BaseModel):
        scenario_name: str
        scenario_description: str

    @classmethod
    def create(cls, description, api=None, chat_format=ChatFormat.ExtendedAlpaca):
        chat = Chat(
            api=api,
            chat_format=chat_format,
            npc=cls.npc,
            player=cls.player,
            scenario=cls.scenario,
            chat_prompt_template=NORMAL_CHAT_PROMPT_TEMPLATE,
            grammar=json_schema_to_gbnf(cls._Scenario.schema_json()),
            response_prefix=''
        )
        result = chat.invoke(description)
        return Scenario(**json.loads(result))


class CreateLoboCharacterByChat:
    format_instructions = PydanticOutputParser(pydantic_object=Character).get_format_instructions()
    prompt_template = ChatPromptTemplate.from_messages([HumanMessage(content="""a furry character"""),
                                                        AIMessage(
                                                            content="""{"character_name":"Seraphina Pawsley","persona":"Seraphina Pawsley, a spirited anthropomorphic red panda, stands at the intersection of human intelligence and the agility of the wild. With a lush coat patterned with fiery hues and cream, she's a vibrant spirit who combines her innate climbing skills with a knack for mechanical invention. Her eyes, a deep emerald, gleam with curiosity and a playful wisdom. She's a master tinkerer, often seen with a tool belt and goggles, ready to leap into adventure or repair a steam-powered contraption in the bustling city of Gearford. Despite her small stature, she's a fierce ally, using her sharp wit and acrobatic prowess to navigate through the urban jungle. Her fluffy ringed tail is not only a symbol of her heritage but serves as a balance aid when she's leaping from rooftop to rooftop, chasing down the latest mystery or invention that's caught her keen eye."}""")])
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

    class _Character(BaseModel):
        character_name: str
        persona: str

    @classmethod
    def create(cls, description, api=None, chat_format=ChatFormat.ExtendedAlpaca):
        chat = Chat(
            api=api,
            chat_format=chat_format,
            npc=cls.npc,
            player=cls.player,
            scenario=cls.scenario,
            chat_prompt_template=NORMAL_CHAT_PROMPT_TEMPLATE,
            grammar=json_schema_to_gbnf(cls._Character.schema_json()),
            response_prefix=''
        )
        result = chat.invoke(description)
        return Character(**json.loads(result))


__all__ = [
    "Chat",
    "Character",
    "Scenario"
]
