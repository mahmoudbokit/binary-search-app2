import redis.asyncio as redis
import json
import os
from typing import Optional, Dict, Any

class RedisDatabase:
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.host = host
        self.port = port
        self.client: Optional[redis.Redis] = None
        self.array_key = "binary_search:array"
        self.metadata_key = "binary_search:metadata"

    async def connect(self):
        """Connect to Redis"""
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        await self.client.ping()

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()

    async def is_connected(self) -> bool:
        """Check Redis connection"""
        try:
            if self.client:
                await self.client.ping()
                return True
            return False
        except:
            return False

    async def save_array(self, array: list):
        """Save array to Redis"""
        if not self.client:
            await self.connect()
        await self.client.set(self.array_key, json.dumps(array))

    async def load_array(self) -> Optional[list]:
        """Load array from Redis"""
        if not self.client:
            await self.connect()
        data = await self.client.get(self.array_key)
        if data:
            return json.loads(data)
        return None

    async def save_array_metadata(self, metadata: Dict[str, Any]):
        """Save array metadata to Redis"""
        if not self.client:
            await self.connect()
        await self.client.set(self.metadata_key, json.dumps(metadata))

    async def load_array_metadata(self) -> Optional[Dict[str, Any]]:
        """Load array metadata from Redis"""
        if not self.client:
            await self.connect()
        data = await self.client.get(self.metadata_key)
        if data:
            return json.loads(data)
        return None

    async def clear_data(self):
        """Clear all data from Redis"""
        if not self.client:
            await self.connect()
        await self.client.delete(self.array_key, self.metadata_key)