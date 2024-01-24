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
    def get_llm_api_base():
        return os.environ['FURCHAIN_TEXT_LLM_API_BASE']

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
