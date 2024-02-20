from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict, messages_from_dict,
)

from furchain.logger import logger


class MongoDBChatMessageHistory(BaseChatMessageHistory):
    """Chat message history that stores history in MongoDB.

    Args:
        connection_string: connection string to connect to MongoDB
        session_id: arbitrary key that is used to store the messages
            of a single chat session.
        database_name: name of the database to use
        collection_name: name of the collection to use
    """

    def __init__(
            self,
            connection_string: str,
            database_name: str,
            collection_name: str,

    ):
        from pymongo import MongoClient, errors

        self.connection_string = connection_string
        self.session_id = None
        self.database_name = database_name
        self.collection_name = collection_name
        self.npc = None
        self.player = None
        self.scenario = None

        try:
            self.client: MongoClient = MongoClient(self.connection_string)
        except errors.ConnectionFailure as error:
            logger.error(error)

        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

    def bind(self, session_id: str, npc: "Character", player: "Character", scenario: "Scenario"):
        self.session_id = session_id
        self.npc = npc
        self.player = player
        self.scenario = scenario
        if session_id is None:
            return self
        self.collection.create_index("session_id", unique=True)
        self.collection.update_one({
            "session_id": self.session_id
        }, {
            "$setOnInsert": {
                "session_id": self.session_id,
                'chat_history': []
            },
            "$set": {
                "npc": self.npc.to_dict(),
                'player': self.player.to_dict(),
                'scenario': self.scenario.to_dict(),
            }
        }, upsert=True)
        return self

    def dict(self) -> dict:
        return self.collection.find_one({"session_id": self.session_id})

    def find(self, session_id, collection_name=None):
        if collection_name is None:
            collection_name = self.collection_name
        return self.db[collection_name].find_one({"session_id": session_id})

    @property
    def chat_history(self) -> List[dict]:
        """Retrieve the chat history from MongoDB"""
        if self.session_id is None:
            return []
        result = self.collection.find_one({"session_id": self.session_id}, {'chat_history': True})
        return result['chat_history']

    @chat_history.setter
    def chat_history(self, value: List[dict]) -> None:
        """Set the chat history in MongoDB"""
        if self.session_id is None:
            return
        self.collection.update_one({"session_id": self.session_id}, {"$set": {"chat_history": value}})

    @property
    def messages(self) -> List[BaseMessage]:
        return messages_from_dict(self.chat_history)

    @messages.setter
    def messages(self, value: List[BaseMessage]) -> None:
        self.chat_history = [message_to_dict(message) for message in value]

    def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in MongoDB"""
        if self.session_id is None:
            return
        self.collection.update_one({
            "session_id": self.session_id
        }, {
            "$push": {
                "chat_history": message_to_dict(message)
            }
        })

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Append the messages to the record in MongoDB"""
        if self.session_id is None:
            return
        self.collection.update_one({
            "session_id": self.session_id
        }, {
            "$push": {
                "chat_history": {
                    "$each": [message_to_dict(message) for message in messages]
                }
            }
        })

    def clear(self) -> None:
        """Clear session memory from MongoDB"""
        if self.session_id is None:
            return
        from pymongo import errors
        try:
            self.collection.update_one({"session_id": self.session_id}, {"$set": {"chat_history": []}})
        except errors.WriteError as err:
            logger.error(err)
