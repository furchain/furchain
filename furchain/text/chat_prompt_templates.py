from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, \
    ChatPromptTemplate

NO_HISTORY_CHAT_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template("""{npc_name}'s Persona: {npc_persona}

{player_name}'s Persona: {player_persona}

Scenario: {scenario_description}"""),
                                                                    HumanMessagePromptTemplate.from_template(
                                                                        """{player_name}: {query}""")])

NORMAL_CHAT_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template("""{npc_name}'s Persona: {npc_persona}

{player_name}'s Persona: {player_persona}

Scenario: {scenario_description}"""),
                                                                MessagesPlaceholder(variable_name='chat_history'),
                                                                HumanMessagePromptTemplate.from_template(
                                                                    """{player_name}: {query}""")])

ROLEPLAY_CHAT_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template("""{npc_name}'s Persona: {npc_persona}

{player_name}'s Persona: {player_persona}

Scenario: {scenario_description}

Play the role of {npc_name}. You must engage in a roleplaying chat with {player_name} below this line. Do not write dialogues and narration for {player_name}. Response should be as detailed as possible."""),
                                                                  MessagesPlaceholder(variable_name='chat_history'),
                                                                  HumanMessagePromptTemplate.from_template(
                                                                      """{player_name}: {query}""")])

CHINESE_TRANSLATION_CHAT_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([SystemMessage(
    content="Translate the following sentences into spoken Chinese with conversational and natural tone. Keep special characters such as * intact."),
    HumanMessage(
        content="*Standing atop a crumbling watchtower, he surveys the vast wilderness ahead*\nThe air is still, as if time itself awaits his next move."),
    AIMessage(
        content="*他站在一座摇摇欲坠的瞭望塔上,眺望着前方广袤无垠的大地*\n空气很静谧,好像时间本身都在等候他的下一步行动."),
    HumanMessage(
        content="*Staring out over the horizon, the old sailor recounts tales of monstrous waves and whispering winds*\nLegends speak of a time when the sea herself was a wild, untamable force, granting fortune to the brave and folly to the foolhardy."),
    AIMessage(
        content="*凝望着地平线,老水手讲述着巨浪和细语风的故事*\n传说描述了一个时代,海洋本身是一股狂野且难以驯服的力量,它赐予勇者财富,而给予鲁莽者愚行的代价."),

    HumanMessage(
        content="In the depths of the ancient forest, where the canopy forms a tapestry of green above and the earthy scent of life fills the air, there exists a quiet understanding between every creature, a silent pact that ensures harmony within the ever-cycling dance of nature."),
    AIMessage(
        content="在这片古老森林的深处,树冠交织成一片绿色的天幕,泥土的生命气息充盈着空气,每一个生灵之间都存在着一种默契的理解,这份无声的协议保证了自然界生生不息舞蹈中的和谐统一."),

    HumanMessage(
        content="*His fingers danced across the piano keys with a passion that could set the night on fire*\nThe melody wove through the room like a ribbon of sound, wrapping the listeners in a warm embrace and carrying them away to a place where only the music mattered."),
    AIMessage(
        content="*他的指尖怀着足以让夜晚燃烧的热情在钢琴键上跳动*\n旋律如同一条声音的缎带,在房间中穿行,将听众们紧紧环绕在一个温暖的怀抱中,带领他们飘向一个只有音乐才是一切的地方."),
    HumanMessage(content="*Fingers trembling, she enters the code into the old terminal*\nIt's now or never."),
    AIMessage(content="*她手指颤抖着,在旧终端输入代码*\n现在做不成,一辈子都不会有机会了."),
    HumanMessagePromptTemplate.from_template("""{query}""")])
