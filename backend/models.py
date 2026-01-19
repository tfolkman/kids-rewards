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
    # chore_id comes from the URL path parameter, not the request body
    # kid_id will be from the authenticated user
    effort_minutes: Optional[int] = Field(default=0, ge=0, le=240)  # How long they worked on it


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
    # Effort tracking fields
    effort_minutes: Optional[int] = Field(default=0, ge=0, le=240)  # Max 4 hours
    retry_count: int = Field(default=0, ge=0)  # Number of retry attempts
    effort_points: int = Field(default=0, ge=0)  # Calculated effort points (0.5 per minute, max 10)
    is_retry: bool = Field(default=False)  # True if this is a retry of a previous attempt

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


class ChoreAssignmentStatus(str, Enum):
    ASSIGNED = "assigned"  # Chore assigned to kid, not yet started
    SUBMITTED = "submitted"  # Kid submitted assignment for approval
    APPROVED = "approved"  # Parent approved, points awarded
    REJECTED = "rejected"  # Parent rejected submission
    OVERDUE = "overdue"  # Past due date without submission


class ChoreAssignmentBase(BaseModel):
    chore_id: str
    assigned_to_kid_id: str
    due_date: datetime
    notes: Optional[str] = None  # Optional notes from parent when assigning


class ChoreAssignmentCreate(ChoreAssignmentBase):
    pass


class ChoreAssignment(ChoreAssignmentBase):
    id: str
    assigned_by_parent_id: str
    chore_name: str  # Denormalized for easier display
    kid_username: str  # Denormalized for easier display
    points_value: int  # Points value at time of assignment
    assignment_status: ChoreAssignmentStatus = ChoreAssignmentStatus.ASSIGNED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    submission_notes: Optional[str] = None  # Notes from kid when submitting
    reviewed_by_parent_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChoreAssignmentSubmission(BaseModel):
    submission_notes: Optional[str] = None
    # assignment_id and kid_id will be from the URL path and authenticated user


# --- Pet Care Module Models ---


class PetSpecies(str, Enum):
    BEARDED_DRAGON = "bearded_dragon"


class BeardedDragonLifeStage(str, Enum):
    BABY = "baby"  # 0-3 months
    JUVENILE = "juvenile"  # 3-12 months
    SUB_ADULT = "sub_adult"  # 12-17 months
    ADULT = "adult"  # 18+ months


class PetCareTaskStatus(str, Enum):
    SCHEDULED = "scheduled"
    ASSIGNED = "assigned"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class CareFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class WeightStatus(str, Enum):
    HEALTHY = "healthy"
    UNDERWEIGHT = "underweight"
    OVERWEIGHT = "overweight"


class PetBase(BaseModel):
    name: str
    species: PetSpecies
    birthday: datetime
    photo_url: Optional[str] = None
    care_notes: Optional[str] = None


class PetCreate(PetBase):
    pass


class Pet(PetBase):
    id: str
    parent_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class PetWithAge(Pet):
    age_months: int
    life_stage: BeardedDragonLifeStage


class PetCareScheduleBase(BaseModel):
    pet_id: str
    task_name: str
    description: Optional[str] = None
    frequency: CareFrequency
    points_value: int = Field(gt=0)
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday (for weekly tasks)
    due_by_time: Optional[str] = None  # "HH:MM" format, e.g., "10:00"


class PetCareScheduleCreate(PetCareScheduleBase):
    assigned_kid_ids: list[str]  # List of kid usernames for rotation


class PetCareSchedule(PetCareScheduleBase):
    id: str
    parent_id: str
    assigned_kid_ids: list[str]
    rotation_index: int = 0  # Current position in rotation
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class PetCareTaskBase(BaseModel):
    schedule_id: str
    pet_id: str
    pet_name: str
    task_name: str
    description: Optional[str] = None
    points_value: int
    assigned_to_kid_id: str
    assigned_to_kid_username: str
    due_date: datetime


class PetCareTaskCreate(PetCareTaskBase):
    pass


class PetCareTask(PetCareTaskBase):
    id: str
    status: PetCareTaskStatus = PetCareTaskStatus.ASSIGNED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    submission_notes: Optional[str] = None
    reviewed_by_parent_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PetCareTaskSubmission(BaseModel):
    notes: Optional[str] = None


class PetHealthLogBase(BaseModel):
    pet_id: str
    weight_grams: int = Field(gt=0)
    notes: Optional[str] = None


class PetHealthLogCreate(PetHealthLogBase):
    pass


class PetHealthLog(PetHealthLogBase):
    id: str
    logged_by_user_id: str
    logged_by_username: str
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    weight_status: Optional[WeightStatus] = None
    life_stage_at_log: Optional[BeardedDragonLifeStage] = None

    class Config:
        from_attributes = True


class CareRecommendation(BaseModel):
    life_stage: BeardedDragonLifeStage
    feeding_frequency: str
    diet_ratio: str
    healthy_weight_range_grams: tuple[int, int]
    care_tips: list[str]


class RecommendedCareSchedule(BaseModel):
    task_name: str
    task_type: str
    frequency: CareFrequency
    points_value: int
    description: str


class ChoreAssignmentApprovalRequest(BaseModel):
    assignment_id: str
    approve: bool  # True to approve, False to reject
    # parent_id will be from the authenticated user
