from furchain.text import Chat, Session, LlamaCpp
from furchain.text.chat_prompt_templates import ROLEPLAY_CHAT_PROMPT_TEMPLATE
from furchain.text.schema import ChatFormat

llm = LlamaCpp(chat_format=ChatFormat.LimaRPExtendedAlpaca)
session = Session.create("As a normal fox, taking adventure in the lost forest, with a fox with magic power.", llm=llm,
                         session_id="adventure_with_fox")
chat = Chat(
    llm=llm.bind(stop=[session.player.character_name + ':']),
    session=session,
    chat_prompt_template=ROLEPLAY_CHAT_PROMPT_TEMPLATE,
)

print(f"[Player] {session.player.character_name}: {session.player.persona}\n")
print(f"[NPC] {session.npc.character_name}: {session.npc.persona}\n")
print(f"[Scenario] {session.scenario.scenario_description})\n")
try:
    while True:
        print('------')
        query = input(session.player.character_name + ": >>>")
        for i in chat.stream(query):
            print(i, end='')
        print()
finally:
    session.clear()
