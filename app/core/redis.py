import redis.asyncio as redis
from fastapi import FastAPI, Depends
from typing import Annotated, AsyncGenerator
from contextlib import asynccontextmanager
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost")
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", "10"))
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", "5"))


settings = Settings()

pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=settings.REDIS_POOL_SIZE,
    socket_timeout=settings.REDIS_TIMEOUT,
    decode_responses=True,  # Auto-decode Redis responses to strings
)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis.from_pool(pool)
    try:
        yield client
    finally:
        await client.close()  # Ensure connection is returned to pool


def get_redis_client() -> redis.Redis:
    """
    Get a Redis client from the pool.
    """
    return redis.Redis(connection_pool=pool)
