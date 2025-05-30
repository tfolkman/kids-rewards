from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    PARENT = "parent"
    KID = "kid"


class FamilyBase(BaseModel):
    name: str


class FamilyCreate(FamilyBase):
    pass


class Family(FamilyBase):
    id: str
    invitation_codes: Optional[dict] = None  # {code: {role, expires, created_by}}

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str


class UserCreate(BaseModel):
    username: str
    password: str
    family_id: Optional[str] = None
    family_name: Optional[str] = None
    invitation_code: Optional[str] = None


class User(UserBase):
    role: UserRole
    id: str
    hashed_password: str
    points: Optional[int] = None
    family_id: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    family_id: Optional[str] = None


class StoreItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    points_cost: int = Field(gt=0)
    family_id: str


class StoreItemCreate(StoreItemBase):
    pass


class StoreItem(StoreItemBase):
    id: str

    class Config:
        from_attributes = True


class PointsAward(BaseModel):
    kid_username: str
    points: int = Field(gt=0)
    reason: Optional[str] = None


class RedemptionRequest(BaseModel):
    item_id: str


class UserPromoteRequest(BaseModel):
    username: str


class PurchaseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class PurchaseLogBase(BaseModel):
    user_id: str
    username: str
    item_id: str
    item_name: str
    points_spent: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: PurchaseStatus = PurchaseStatus.PENDING
    family_id: str


class PurchaseLogCreate(PurchaseLogBase):
    pass


class PurchaseLog(PurchaseLogBase):
    id: str

    class Config:
        from_attributes = True


class ChoreStatus(str, Enum):
    AVAILABLE = "available"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ChoreBase(BaseModel):
    name: str
    description: Optional[str] = None
    points_value: int = Field(gt=0)


class ChoreCreate(ChoreBase):
    pass


class ChoreUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    points_value: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class Chore(ChoreBase):
    id: str
    created_by_parent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        from_attributes = True


class ChoreSubmission(BaseModel):
    chore_id: str


class ChoreApprovalRequest(BaseModel):
    chore_log_id: str
    approve: bool


class ChoreLogBase(BaseModel):
    chore_id: str
    chore_name: str
    kid_id: str
    kid_username: str
    points_value: int
    status: ChoreStatus
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by_parent_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChoreLogCreate(BaseModel):
    chore_id: str
    user_id: Optional[str] = None  # This should be the username of the kid, or 'current' for self


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
    requester_username: str
    request_type: RequestType
    details: dict
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class RequestCreate(BaseModel):
    item_id: str


class Request(RequestBase):
    id: str
    reviewed_by_parent_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class RequestStatusUpdate(BaseModel):
    new_status: RequestStatus


class InvitationCreate(BaseModel):
    role: UserRole = UserRole.KID  # Default to kid role


class InvitationInfo(BaseModel):
    code: str
    role: UserRole
    expires: datetime
    created_by: str
    created_at: datetime


class FamilyMembers(BaseModel):
    family: Family
    members: List[User]
