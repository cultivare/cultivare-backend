from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.DATABASE_NAME]
        self.cultures_collection = self.db[settings.CULTURES_COLLECTION_NAME]
        self.notes_collection = self.db[settings.NOTES_COLLECTION_NAME]


db = MongoDB()
