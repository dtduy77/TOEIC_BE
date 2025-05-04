import redis
from app.core.config import get_settings
import json
from typing import Any, Optional, Union

settings = get_settings()

# Initialize Redis connection
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True  # Automatically decode responses to Python strings
)

def set_token_cache(user_id: str, token: str, expires_in: int) -> None:
    """
    Store a user's token in Redis cache
    
    Args:
        user_id: The user's unique identifier
        token: The access token to cache
        expires_in: Time in seconds until the token expires
    """
    key = f"user_token:{user_id}"
    redis_client.setex(key, expires_in, token)

def get_token_cache(user_id: str) -> Optional[str]:
    """
    Retrieve a user's token from Redis cache
    
    Args:
        user_id: The user's unique identifier
        
    Returns:
        The cached token or None if not found/expired
    """
    key = f"user_token:{user_id}"
    return redis_client.get(key)

def delete_token_cache(user_id: str) -> None:
    """
    Delete a user's token from Redis cache (e.g., on logout)
    
    Args:
        user_id: The user's unique identifier
    """
    key = f"user_token:{user_id}"
    redis_client.delete(key)

def set_cache(key: str, data: Any, expires_in: int = 3600) -> None:
    """
    Store any data in Redis cache with expiration
    
    Args:
        key: Cache key
        data: Data to cache (will be JSON serialized)
        expires_in: Time in seconds until the data expires (default: 1 hour)
    """
    serialized_data = json.dumps(data)
    redis_client.setex(key, expires_in, serialized_data)

def get_cache(key: str) -> Optional[Any]:
    """
    Retrieve data from Redis cache
    
    Args:
        key: Cache key
        
    Returns:
        The cached data (JSON deserialized) or None if not found/expired
    """
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def delete_cache(key: str) -> None:
    """
    Delete data from Redis cache
    
    Args:
        key: Cache key
    """
    redis_client.delete(key)
