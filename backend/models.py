from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class UserRole(str, Enum):
    PARENT = "parent"
    KID = "kid"

class UserBase(BaseModel):
    username: str
    role: UserRole

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str # Or int, depending on DB
    hashed_password: str
    points: Optional[int] = None # Only applicable for kids

    class Config:
        orm_mode = True # Changed from from_attributes for Pydantic v2
        # For Pydantic v1, use: from_attributes = True

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
        orm_mode = True # Changed from from_attributes for Pydantic v2
        # For Pydantic v1, use: from_attributes = True

class PointsAward(BaseModel):
    kid_username: str
    points: int = Field(gt=0)
    reason: Optional[str] = None

class RedemptionRequest(BaseModel):
    item_id: str # Or int