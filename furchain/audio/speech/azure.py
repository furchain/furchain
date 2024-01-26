import azure.cognitiveservices.speech as speechsdk

from furchain.audio.schema import ParrotTTS
from furchain.config import AudioConfig

AzureResponseFormat = speechsdk.enums.SpeechSynthesisOutputFormat

response_format_mapping = {
    'mp3': AzureResponseFormat.Audio24Khz96KBitRateMonoMp3,
    'opus': AzureResponseFormat.Ogg24Khz16BitMonoOpus,
    'wav': AzureResponseFormat.Riff44100Hz16BitMonoPcm,
}


class AzureTTS(ParrotTTS):
    default_speaker = "zh-CN-YunyiMultilingualNeural"

    @classmethod
    def run(cls, text: str, speaker: str = "zh-CN-YunyiMultilingualNeural", style: str = None,
            response_format: str | speechsdk.enums.SpeechSynthesisOutputFormat = 'mp3') -> bytes:
        speech_config = speechsdk.SpeechConfig(subscription=AudioConfig.get_azure_subscription(),
                                               region=AudioConfig.get_azure_region())
        speech_config.speech_synthesis_voice_name = speaker
        speech_config.set_speech_synthesis_output_format(
            response_format_mapping[response_format] if isinstance(response_format, str) else response_format)
        stream = speechsdk.audio.PullAudioOutputStream()
        audio_config = speechsdk.audio.AudioOutputConfig(stream=stream)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        return speech_synthesizer.speak_text(text).audio_data
