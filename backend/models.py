from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    PARENT = "parent"
    KID = "kid"

class UserBase(BaseModel):
    username: str
    # role: UserRole # Role will be part of User model, not necessarily UserBase for creation

class UserCreate(BaseModel): # No longer inherits UserBase directly if role is removed for creation
    username: str
    password: str

class User(UserBase): # User still has a role
    role: UserRole
    id: str # Or int, depending on DB
    hashed_password: str
    points: Optional[int] = None # Only applicable for kids

    class Config:
        from_attributes = True # For Pydantic V2
        # orm_mode = True # For Pydantic V1

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class StoreItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    points_cost: int = Field(gt=0)

class StoreItemCreate(StoreItemBase):
    pass

class StoreItem(StoreItemBase):
    id: str # Or int

    class Config:
        from_attributes = True # For Pydantic V2
        # orm_mode = True # For Pydantic V1

class PointsAward(BaseModel):
    kid_username: str
    points: int = Field(gt=0)
    reason: Optional[str] = None

class RedemptionRequest(BaseModel):
    item_id: str # Or int

class UserPromoteRequest(BaseModel):
    username: str
