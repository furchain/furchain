from furchain.text import Character, Scenario, Chat, Session, LlamaCpp
from furchain.text.chat_prompt_templates import ROLEPLAY_CHAT_PROMPT_TEMPLATE

llm = LlamaCpp()
player = Character.create("a normal fox", llm=llm)
npc = Character.create("a fox with magic power", llm=llm)
scenario = Scenario.create("adventure in the lost forest", llm=llm)
session = Session(
    session_id="chat_with_fox",
    player=player,
    npc=npc,
    scenario=scenario
)
chat = Chat(
    llm=llm,
    session=session,
    scenario=scenario,
    chat_prompt_template=ROLEPLAY_CHAT_PROMPT_TEMPLATE,
    response_prefix=npc.character_name + ":",
    stop=[player.character_name + ":"]  # prevent the player from talking
)

print(f"Player (You): {player.character_name}, {player.persona}")
print(f"NPC: {npc.character_name}, {npc.persona}")
print(f"Scenario: {scenario.scenario_description})")
while True:
    print('------')
    query = input(player.character_name + ": >>>")
    for i in chat.stream(query):
        print(i, end='')
    print()
