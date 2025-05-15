from fastapi import APIRouter, Depends, HTTPException
from pydantic.networks import EmailStr

from app.api.deps import RedisClientDep, get_current_active_superuser
from app.models import Message
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check")
async def health_check() -> bool:
    return True


@router.get("/test-redis")
async def test_redis(redis_client: RedisClientDep) -> bool:
    """
    Test Redis connection.
    """
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis connection failed: {e}")


@router.get("/set-redis")
async def set_redis(redis_client: RedisClientDep, key: str, value: str) -> Message:
    """
    Set a key-value pair in Redis.
    """
    try:
        await redis_client.set(key, value)
        return Message(message=f"Key {key} set to {value}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set Redis key: {e}")


@router.get("/get-redis")
async def get_redis(redis_client: RedisClientDep, key: str) -> Message:
    """
    Get a value from Redis by key.
    """
    try:
        value = await redis_client.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Key {key} not found")
        return Message(message=f"Value for {key}: {value}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Redis key: {e}")


# get all redis keys
@router.get("/get-all-redis-keys")
async def get_all_redis_keys(redis_client: RedisClientDep) -> Message:
    """
    Get all keys from Redis.
    """
    try:
        keys = await redis_client.keys("*")
        return Message(message=f"All Redis keys: {keys}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Redis keys: {e}")
