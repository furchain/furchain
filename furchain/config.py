import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class TextConfig:

    @staticmethod
    def get_mongo_url():
        return os.environ['FURCHAIN_TEXT_MONGO_URL']

    @staticmethod
    def get_mongo_db():
        return os.environ['FURCHAIN_TEXT_MONGO_DB']

    @staticmethod
    def get_mongo_character_collection():
        return os.environ['FURCHAIN_TEXT_MONGO_CHARACTER_COLLECTION']

    @staticmethod
    def get_mongo_scenario_collection():
        return os.environ['FURCHAIN_TEXT_MONGO_SCENARIO_COLLECTION']

    @staticmethod
    def get_llama_cpp_api_base():
        return os.environ['FURCHAIN_TEXT_LLAMA_CPP_API_BASE']

    @staticmethod
    def get_player_name():
        return os.environ['FURCHAIN_TEXT_PLAYER_NAME']

    @staticmethod
    def get_player_persona():
        return os.environ['FURCHAIN_TEXT_PLAYER_PERSONA']

    @staticmethod
    def get_npc_name():
        return os.environ['FURCHAIN_TEXT_NPC_NAME']

    @staticmethod
    def get_npc_persona():
        return os.environ['FURCHAIN_TEXT_NPC_PERSONA']

    @staticmethod
    def get_scenario_description():
        return os.environ['FURCHAIN_TEXT_SCENARIO_DESCRIPTION']


class AudioConfig:

    @staticmethod
    def get_gpt_sovits_api_base():
        return os.environ['FURCHAIN_AUDIO_GPT_SOVITS_API_BASE']

    @staticmethod
    def get_sovits_api():
        return os.environ['FURCHAIN_AUDIO_SOVITS_API']

    @staticmethod
    def get_rvc_api():
        return os.environ['FURCHAIN_AUDIO_RVC_API']

    @staticmethod
    def get_azure_subscription():
        return os.environ['FURCHAIN_AUDIO_AZURE_SUBSCRIPTION']

    @staticmethod
    def get_azure_region():
        return os.environ['FURCHAIN_AUDIO_AZURE_REGION']

    @staticmethod
    def get_funasr_api():
        return os.environ['FURCHAIN_AUDIO_FUNASR_API']

class ImageConfig:

    @classmethod
    def get_stable_diffusion_webui_api_base(cls):
        return os.environ['FURCHAIN_IMAGE_STABLE_DIFFUSION_WEBUI_API_BASE']