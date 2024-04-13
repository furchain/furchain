from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict, messages_from_dict,
)

from furchain.logger import logger


class MongoDBChatMessageHistory(BaseChatMessageHistory):
    """
    A class that represents a chat message history stored in MongoDB.

    Attributes:
        connection_string (str): The connection string for the MongoDB database.
        database_name (str): The name of the database.
        collection_name (str): The name of the collection.
        session_id (str): The session ID.
        npc (Character): The NPC character.
        player (Character): The player character.
        scenario (Scenario): The scenario.
        client (MongoClient): The MongoDB client.
        db (Database): The MongoDB database.
        collection (Collection): The MongoDB collection.

    Methods:
        bind(session_id: str, npc: "Character", player: "Character", scenario: "Scenario"): Binds the chat message history to a session.
        dict() -> dict: Returns a dictionary representation of the chat message history.
        find(session_id, collection_name=None): Finds a chat message history by session ID.
        chat_history() -> List[dict]: Returns the chat history.
        chat_history(value: List[dict]): Sets the chat history.
        messages() -> List[BaseMessage]: Returns the messages.
        messages(value: List[BaseMessage]): Sets the messages.
        add_message(message: BaseMessage): Adds a message to the chat history.
        add_messages(messages: List[BaseMessage]): Adds multiple messages to the chat history.
        clear(): Clears the chat history.
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
        """
        Binds the chat message history to a session.

        Args:
            session_id (str): The session ID.
            npc (Character): The NPC character.
            player (Character): The player character.
            scenario (Scenario): The scenario.

        Returns:
            MongoDBChatMessageHistory: The chat message history.
        """
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
        """
        Returns a dictionary representation of the chat message history.

        Returns:
            dict: A dictionary representation of the chat message history.
        """
        return self.collection.find_one({"session_id": self.session_id}) or {
            "session_id": self.session_id,
            "npc": self.npc.to_dict(),
            "player": self.player.to_dict(),
            "scenario": self.scenario.to_dict(),
            "chat_history": self.chat_history
        }


    def find(self, session_id, collection_name=None):
        """
        Finds a chat message history by session ID.

        Args:
            session_id (str): The session ID.
            collection_name (str, optional): The collection name. Defaults to None.

        Returns:
            dict: The chat message history.
        """
        if collection_name is None:
            collection_name = self.collection_name
        return self.db[collection_name].find_one({"session_id": session_id})

    @property
    def chat_history(self) -> List[dict]:
        """
        Returns the chat history.

        Returns:
            List[dict]: The chat history.
        """
        if self.session_id is None:
            return []
        result = self.collection.find_one({"session_id": self.session_id}, {'chat_history': True})
        return result['chat_history']

    @chat_history.setter
    def chat_history(self, value: List[dict]) -> None:
        """
        Sets the chat history.

        Args:
            value (List[dict]): The chat history.
        """
        if self.session_id is None:
            return
        self.collection.update_one({"session_id": self.session_id}, {"$set": {"chat_history": value}})

    @property
    def messages(self) -> List[BaseMessage]:
        """
        Returns the messages.

        Returns:
            List[BaseMessage]: The messages.
        """
        return messages_from_dict(self.chat_history)

    @messages.setter
    def messages(self, value: List[BaseMessage]) -> None:
        """
        Sets the messages.

        Args:
            value (List[BaseMessage]): The messages.
        """
        self.chat_history = [message_to_dict(message) for message in value]

    def add_message(self, message: BaseMessage) -> None:
        """
        Adds a message to the chat history.

        Args:
            message (BaseMessage): The message.
        """
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
        """
        Adds multiple messages to the chat history.

        Args:
            messages (List[BaseMessage]): The messages.
        """
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
        """
        Clears the chat history.
        """
        if self.session_id is None:
            return
        from pymongo import errors
        try:
            self.collection.update_one({"session_id": self.session_id}, {"$set": {"chat_history": []}})
        except errors.WriteError as err:
            logger.error(err)


__all__ = [
    "MongoDBChatMessageHistory"
]
