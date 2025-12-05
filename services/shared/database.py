"""
Database Connection Module.
Handles MongoDB connection for application data (Users, Projects, API Keys).
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional

logger = logging.getLogger("watchllm.database")

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    def connect(self):
        """Connect to MongoDB."""
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DB_NAME", "watchllm")
        
        try:
            self.client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[db_name]
            logger.info(f"Connected to MongoDB at {mongo_url}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionFailure, ServerSelectionTimeoutError, OSError)),
        reraise=True
    )
    async def ping(self):
        """Verify connection to MongoDB."""
        if not self.client:
            self.connect()
        
        logger.info("Pinging MongoDB...")
        await self.client.admin.command('ping')
        logger.info("✅ MongoDB connection verified")

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

db = Database()

async def get_db():
    """Dependency for FastAPI."""
    if db.client is None:
        db.connect()
    return db.db
