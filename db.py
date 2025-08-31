"""Database layer (Motor, MongoDB).

Contains initialization, access, and shutdown handling for MongoDB.
Supports TLS options for Atlas (Windows).
"""

import os
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

# Ensure .env values take precedence over existing env vars in this dev setup
load_dotenv(override=True)

_MONGO_CLIENT: Optional[AsyncIOMotorClient] = None
_DB: Optional[AsyncIOMotorDatabase] = None

# Centralized collection names
COLLECTION_ARTICLES = "articles"


def get_mongo_uri() -> str:
    """Read the MongoDB URI from environment variables.

    Raises:
        RuntimeError: If the variable is not set.
    """
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI environment variable is not set")
    return uri


def get_db_name() -> str:
    """Read the database name from environment variables.

    Raises:
        RuntimeError: If the variable is not set.
    """
    name = os.getenv("MONGODB_DB_NAME")
    if not name:
        raise RuntimeError("MONGODB_DB_NAME environment variable is not set")
    return name


async def init_db() -> AsyncIOMotorDatabase:
    """Initialize the connection and create required indexes.

    Returns:
        AsyncIOMotorDatabase: Reference to the configured database.
    """
    global _MONGO_CLIENT, _DB
    if _DB is not None:
        return _DB

    uri = get_mongo_uri()
    db_name = get_db_name()

    # TLS options for Atlas on Windows
    client_kwargs: Dict[str, Any] = {}
    allow_invalid = os.getenv("MONGODB_TLS_ALLOW_INVALID_CERTS", "false").lower() in {"1", "true", "yes"}
    if allow_invalid:
        client_kwargs["tlsAllowInvalidCertificates"] = True

    ca_bundle = os.getenv("MONGODB_TLS_CA_BUNDLE")
    use_certifi = os.getenv("MONGODB_USE_CERTIFI", "true").lower() in {"1", "true", "yes"}
    if ca_bundle:
        client_kwargs["tlsCAFile"] = ca_bundle
    elif use_certifi:
        try:
            import certifi  # type: ignore
            client_kwargs["tlsCAFile"] = certifi.where()
        except Exception:
            # Fall back silently if certifi not available
            pass

    _MONGO_CLIENT = AsyncIOMotorClient(uri, **client_kwargs)
    _DB = _MONGO_CLIENT[db_name]

    # Ensure indexes (once)
    await _DB[COLLECTION_ARTICLES].create_index("title", unique=True)

    return _DB


def get_db() -> AsyncIOMotorDatabase:
    """Return the initialized database instance.

    Raises:
        RuntimeError: If init_db() has not been called yet.
    """
    if _DB is None:
        raise RuntimeError("Database not initialized. Call init_db() at startup.")
    return _DB


async def close_db() -> None:
    """Close the database connection (e.g., on shutdown)."""
    global _MONGO_CLIENT, _DB
    if _MONGO_CLIENT is not None:
        _MONGO_CLIENT.close()
    _MONGO_CLIENT = None
    _DB = None
