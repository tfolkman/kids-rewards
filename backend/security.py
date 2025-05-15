import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Configuration
SECRET_KEY = os.getenv("APP_SECRET_KEY")
if not SECRET_KEY:
    # For a Lambda, failing to start if the key isn't set is a safe default.
    # This ensures the application doesn't run with an insecure default key.
    raise ValueError("CRITICAL: APP_SECRET_KEY environment variable is not set. Application cannot start securely.")
if len(SECRET_KEY) < 32:
    raise ValueError("CRITICAL: APP_SECRET_KEY must be at least 32 characters long for security.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    verification_result = pwd_context.verify(plain_password, hashed_password)
    logger.info(f"Password verification result: {verification_result}")
    return verification_result


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None
