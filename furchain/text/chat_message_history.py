from typing import List

import pymongo
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
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
            session_id: str,
            database_name: str,
            collection_name: str,
            npc_name: str,
            player_name: str,
            scenario_name: str,

    ):
        from pymongo import MongoClient, errors

        self.connection_string = connection_string
        self.session_id = session_id
        self.database_name = database_name
        self.collection_name = collection_name
        self.npc_name = npc_name
        self.player_name = player_name
        self.scenario_name = scenario_name

        try:
            self.client: MongoClient = MongoClient(connection_string)
        except errors.ConnectionFailure as error:
            logger.error(error)

        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.collection.create_index("session_id")

    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore
        """Retrieve the messages from MongoDB"""
        from pymongo import errors

        try:
            cursor = self.collection.find({"session_id": self.session_id}).sort('_id', pymongo.ASCENDING)
        except errors.OperationFailure as error:
            logger.error(error)
            raise error

        if cursor:
            items = [document["message"] for document in cursor]
        else:
            items = []

        messages = messages_from_dict(items)
        return messages

    def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in MongoDB"""
        from pymongo import errors

        try:
            self.collection.insert_one(
                {
                    "session_id": self.session_id,
                    "message": message_to_dict(message),
                }
            )
        except errors.WriteError as err:
            logger.error(err)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Append the messages to the record in MongoDB"""
        from pymongo import errors

        try:
            self.collection.insert_many(
                [
                    {
                        "session_id": self.session_id,
                        "message": message_to_dict(message),
                    }
                    for message in messages
                ]
            )
        except errors.WriteError as err:
            logger.error(err)

    def clear(self) -> None:
        """Clear session memory from MongoDB"""
        from pymongo import errors

        try:
            self.collection.delete_many({"session_id": self.session_id})
        except errors.WriteError as err:
            logger.error(err)
