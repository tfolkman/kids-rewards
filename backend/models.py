from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    PARENT = "parent"
    KID = "kid"


class UserBase(BaseModel):
    username: str
    # role: UserRole # Role will be part of User model, not necessarily UserBase for creation


class UserCreate(BaseModel):  # No longer inherits UserBase directly if role is removed for creation
    username: str
    password: str


class User(UserBase):  # User still has a role
    role: UserRole
    id: str  # Or int, depending on DB
    hashed_password: str
    points: Optional[int] = None  # Only applicable for kids

    class Config:
        from_attributes = True  # For Pydantic V2
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
    id: str  # Or int

    class Config:
        from_attributes = True  # For Pydantic V2
        # orm_mode = True # For Pydantic V1


class PointsAward(BaseModel):
    kid_username: str
    points: int = Field(gt=0)
    reason: Optional[str] = None


class RedemptionRequest(BaseModel):
    item_id: str  # Or int


class UserPromoteRequest(BaseModel):
    username: str


class PurchaseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"  # Default for now, will change with approval system


class PurchaseLogBase(BaseModel):
    user_id: str
    username: str
    item_id: str
    item_name: str
    points_spent: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: PurchaseStatus = PurchaseStatus.PENDING


class PurchaseLogCreate(PurchaseLogBase):
    pass


class PurchaseLog(PurchaseLogBase):
    id: str  # Or int, depending on DB

    class Config:
        from_attributes = True


class ChoreStatus(str, Enum):
    AVAILABLE = "available"  # Chore is available for kids to do
    PENDING_APPROVAL = "pending_approval"  # Kid submitted chore, awaiting parent approval
    APPROVED = "approved"  # Parent approved, points awarded
    REJECTED = "rejected"  # Parent rejected
    # COMPLETED might be redundant if APPROVED means completed and awarded.
    # ARCHIVED could be for chores no longer active but kept for history.


class ChoreBase(BaseModel):
    name: str
    description: Optional[str] = None
    points_value: int = Field(gt=0)
    # created_by_parent_id: str # This will be derived from the authenticated user


class ChoreCreate(ChoreBase):
    pass


class Chore(ChoreBase):
    id: str
    created_by_parent_id: str  # User ID of the parent who created it
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True  # To allow deactivating chores instead of hard delete

    class Config:
        from_attributes = True


class ChoreSubmission(BaseModel):
    chore_id: str
    # kid_id will be from the authenticated user


class ChoreApprovalRequest(BaseModel):
    chore_log_id: str
    approve: bool  # True to approve, False to reject
    # parent_id will be from the authenticated user


class ChoreLogBase(BaseModel):
    chore_id: str
    chore_name: str  # Denormalized for easier display
    kid_id: str
    kid_username: str  # Denormalized
    points_value: int  # Points for this specific instance of chore completion
    status: ChoreStatus
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by_parent_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChoreLogCreate(ChoreLogBase):
    pass


class ChoreLog(ChoreLogBase):
    id: str


class RequestType(str, Enum):
    ADD_STORE_ITEM = "add_store_item"
    ADD_CHORE = "add_chore"
    OTHER = "other"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequestBase(BaseModel):
    requester_id: str
    requester_username: str  # Denormalized for easier display
    request_type: RequestType
    details: dict  # Flexible field for request specifics
    # Example for ADD_STORE_ITEM: {"name": "...", "description": "...", "points_cost": ...}
    # Example for ADD_CHORE: {"name": "...", "description": "...", "points_value": ...}
    # Example for OTHER: {"message": "..."}
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class RequestCreate(RequestBase):
    pass


class Request(RequestBase):
    id: str
    reviewed_by_parent_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
