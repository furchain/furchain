from furchain.audio.conversion.rvc import RVC
from furchain.audio.utils.audio_editor import AudioEditor
from furchain.audio.utils.audio_separator import AudioSeparator
from furchain.audio.utils.play import play_audio_bytes

music = "blackpink.mp3"
target_singer = "taylor_swift"

rvc = RVC(speaker=target_singer)

for vocal, bgm in AudioSeparator(filename=music):
    new_vocal = rvc.invoke(vocal)
    audio = AudioEditor.merge(new_vocal, bgm)
    play_audio_bytes(audio)
