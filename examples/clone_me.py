import io

import pydub

from furchain.audio.speech.gpt_sovits import GPTSovits
from furchain.audio.transcriptions.funasr import FunASR
from furchain.audio.utils.microphone import Microphone
from furchain.audio.utils.play import play_audio_bytes
from furchain.text import Chat, LlamaCpp, Session


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


language = input("""Which language do you speak?
1. English
2. Chinese

Please enter 1 or 2.
>>> """)

if language == '1':
    language = 'en'
else:
    language = 'zh'

print_color("""Introduce yourself to your microphone. Press Ctrl+C when you finish.""", Colors.RED)
result = ''
buffer = io.BytesIO()
microphone = Microphone()
with microphone as microphone_stream:
    def double_write_stream(stream, buffer):
        for i in stream:
            buffer.write(i)
            yield i


    try:
        for i in FunASR(mode='offline').stream(double_write_stream(microphone_stream, buffer)):
            print(i['text'], end='')
            result += i['text']
            if '.' in i['text'] or '。' in i['text']:
                print()
    except KeyboardInterrupt:
        microphone.stop()
        buffer.flush()
        print("\nFinish recording.")

print('------')
print_color(result, Colors.GREEN)
print('------')
with open("data/gpt-sovits/clone_me.wav", "wb") as f:
    pydub.AudioSegment(
        data=buffer.getvalue(),
        sample_width=2,
        frame_rate=16000,
        channels=1,
    ).export(f, format='wav')
gpt_sovits = GPTSovits(refer_wav_path='clone_me.wav', prompt_text=result, prompt_language=language)
llm = LlamaCpp()
print_color("Cloning your persona, please wait...", Colors.RED)
session = Session.create(
    "The player is talking to the clone of the player self. Here is self-introduction of the player: " + result,
    llm=llm, session_id=None)
chat = Chat(session=session, llm=llm)
result = ''
for i in chat.stream("Hello, who are you?"):
    print_color(i, Colors.GREEN, end='')
    result += i
    if '.' in i or '。' in i:
        print()
if '.' in result:
    for j in result.split('.')[:-1]:
        play_audio_bytes(gpt_sovits.invoke({"text": j, "text_language": 'en'}))
else:
    for j in result.split('。')[:-1]:
        play_audio_bytes(gpt_sovits.invoke({"text": j, "text_language": 'en'}))
