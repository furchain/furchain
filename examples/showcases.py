# ANSI escape codes for some colors
import os


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'


# Function to print text in color
def print_color(text, color, **kwargs):
    print(color + str(text) + Colors.RESET, **kwargs)


# Download LLM model
from huggingface_hub import hf_hub_download

REPO_ID = "Nan-Do/FusionNet_7Bx2_MoE_14B-GGUF"
FILENAME = "FusionNet_7Bx2_MoE_14B-Q4_K.gguf"
if not os.path.exists(f"./data/llama-cpp/{FILENAME}"):
    print_color(f"Downloading {FILENAME}, it may take a while...", Colors.CYAN)
    hf_hub_download(repo_id=REPO_ID, filename=FILENAME, local_dir="./data/llama-cpp", local_dir_use_symlinks=False)

# Download reference audio
import requests

with open("./data/gpt-sovits/reference.wav", "wb") as f:
    f.write(requests.get(
        "https://huggingface.co/spaces/XzJosh/badXT-GPT-SoVITS/resolve/main/audio/Taffy/Taffy_100.wav").content)

# Play audio bytes
with open("./data/gpt-sovits/reference.wav", 'rb') as f:
    audio_bytes = f.read()
from furchain.audio.utils.play import play_audio_bytes

print_color("Playing reference audio...", Colors.CYAN)
play_audio_bytes(audio_bytes)

# Transcribe audio
from furchain.audio.transcriptions.funasr import FunASR
from furchain.audio.utils.convert import convert_to_pcm

audio_transcript = FunASR().invoke(convert_to_pcm(audio_bytes))['text']
print_color(f"{audio_transcript=}", Colors.CYAN)

# Generate text
from furchain.text.schema import LlamaCpp, Chat, Character, Scenario, Session

llm = LlamaCpp()
session = Session(session_id=None)
chat = Chat(llm=llm, session=session)
print_color("Ask LLM to calculate 1+1", Colors.CYAN)
print_color(chat.invoke("calculate 1+1"), Colors.GREEN)

# Roleplay
player = Character.from_file("./presets/characters/Dash Howler.json")
npc = Character.from_file("./presets/characters/Zane Ryder.json")
scenario = Scenario.from_file("./presets/scenarios/Beneath the Starlit Sky.json")
session = Session(session_id="test_roleplay", player=player, npc=npc, scenario=scenario)
chat = Chat(llm=llm, session=session)
print_color("Engage into a roleplay game, ask for npc's plan for the night. Non-stream.", Colors.CYAN)
text_stream = chat.stream("What's your plan for the night?")
text = ''
import time

start_time = time.time()
for i in text_stream:
    text += i
    print_color(i, Colors.GREEN, end='')
    if '.' in i or '\n' in i:
        print()
print()

# Roleplay with audio
from furchain.audio.speech.gpt_sovits import GPTSovits

gpt_sovits = GPTSovits(refer_wav_path='reference.wav', prompt_text=audio_transcript, prompt_language='zh')
audio_bytes = gpt_sovits.invoke({"text": text, "text_language": "en"})
print_color(f"[Non-Stream] Complete Response Time Cost: {time.time() - start_time}", Colors.BLUE)
play_audio_bytes(audio_bytes)

# Stream audio
from furchain.utils.broadcaster import iterator_callback_broadcaster
from furchain.text.output_parsers import SentenceStreamOutputParser

print_color("Ask npc about his plan for tomorrow", Colors.CYAN)
sentence_stream = (chat | SentenceStreamOutputParser()).stream("What's your plan for tomorrow?  Tell me in detail.")
sentence_iterator, audio_iterator = iterator_callback_broadcaster(sentence_stream, [
    lambda x: print_color(x, Colors.GREEN) if x else None,
                                                                                    lambda x: gpt_sovits.invoke(
                                                                                        {"text": x,
                                                                                         "text_language": "en"}) if x else None])
start_time = time.time()
for audio in audio_iterator:
    if audio:
        print_color(f"[Stream] One Sentence Response Time Cost: {time.time() - start_time}", Colors.BLUE)
        play_audio_bytes(audio)
        start_time = time.time()
print()

# Microphone input
from furchain.audio.utils.microphone import Microphone

query = ''
print_color("Continue this conversation by speaking with your microphone. Say `over` or `结束` to send the message.",
            Colors.RED)
with Microphone() as microphone_stream:
    for i in FunASR(mode='2pass').stream(microphone_stream):
        query += i['text']
        print_color(i, Colors.YELLOW)
        if "over" in i['text'] or "结束" in i['text']:
            query.replace("over", '').replace("结束", '')
            break

sentence_stream = (chat | SentenceStreamOutputParser()).stream(query)
sentence_iterator, audio_iterator = iterator_callback_broadcaster(sentence_stream, [lambda x: x,
                                                                                    lambda x: gpt_sovits.invoke(
                                                                                        {"text": x,
                                                                                         "text_language": "en"}) if x else None])
for audio in audio_iterator:
    if audio:
        print_color(audio, Colors.CYAN)
        play_audio_bytes(audio)
