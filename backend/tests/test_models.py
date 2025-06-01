from models import (
    PointsAward,
    PurchaseLog,
    PurchaseLogBase,
    PurchaseLogCreate,
    PurchaseStatus,
    RedemptionRequest,
    StoreItem,
    StoreItemBase,
    StoreItemCreate,
    Token,
    TokenData,
    User,
    UserBase,
    UserCreate,
    UserPromoteRequest,
    UserRole,
)


def test_user_role_enum():
    assert UserRole.PARENT == "parent"
    assert UserRole.KID == "kid"


def test_user_base_model():
    user_base = UserBase(username="testuser")
    assert user_base.username == "testuser"


def test_user_create_model():
    user_create = UserCreate(username="testuser", password="testpassword")
    assert user_create.username == "testuser"
    assert user_create.password == "testpassword"


def test_user_model():
    user = User(role=UserRole.KID, id="testuser", username="testuser", hashed_password="testhashedpassword", points=100)
    assert user.role == UserRole.KID
    assert user.id == "testuser"
    assert user.username == "testuser"
    assert user.hashed_password == "testhashedpassword"
    assert user.points == 100


def test_user_model_with_family_id():
    # Test user with family_id
    user_with_family = User(
        role=UserRole.KID,
        id="testuser",
        username="testuser",
        hashed_password="testhashedpassword",
        points=100,
        family_id="family-123"
    )
    assert user_with_family.family_id == "family-123"

    # Test parent user with family_id
    parent_user = User(
        role=UserRole.PARENT,
        id="parentuser",
        username="parentuser",
        hashed_password="parenthashed",
        family_id="family-456"
    )
    assert parent_user.family_id == "family-456"
    assert parent_user.points is None  # Parents don't have points

    # Test user without family_id (backward compatibility)
    user_no_family = User(
        role=UserRole.KID,
        id="olduser",
        username="olduser",
        hashed_password="oldhashed",
        points=50
    )
    assert user_no_family.family_id is None


def test_token_model():
    token = Token(access_token="testtoken", token_type="bearer")
    assert token.access_token == "testtoken"
    assert token.token_type == "bearer"


def test_token_data_model():
    token_data = TokenData(username="testuser")
    assert token_data.username == "testuser"


def test_store_item_base_model():
    store_item_base = StoreItemBase(name="testitem", points_cost=50)
    assert store_item_base.name == "testitem"
    assert store_item_base.points_cost == 50


def test_store_item_create_model():
    store_item_create = StoreItemCreate(name="testitem", points_cost=50)
    assert store_item_create.name == "testitem"
    assert store_item_create.points_cost == 50


def test_store_item_model():
    store_item = StoreItem(id="testitemid", name="testitem", points_cost=50)
    assert store_item.id == "testitemid"
    assert store_item.name == "testitem"
    assert store_item.points_cost == 50


def test_points_award_model():
    points_award = PointsAward(kid_username="testkid", points=25)
    assert points_award.kid_username == "testkid"
    assert points_award.points == 25


def test_redemption_request_model():
    redemption_request = RedemptionRequest(item_id="testitemid")
    assert redemption_request.item_id == "testitemid"


def test_user_promote_request_model():
    user_promote_request = UserPromoteRequest(username="testuser")
    assert user_promote_request.username == "testuser"


def test_purchase_status_enum():
    assert PurchaseStatus.PENDING == "pending"
    assert PurchaseStatus.APPROVED == "approved"
    assert PurchaseStatus.REJECTED == "rejected"
    assert PurchaseStatus.COMPLETED == "completed"


def test_purchase_log_base_model():
    purchase_log_base = PurchaseLogBase(
        user_id="testuser", username="testuser", item_id="testitem", item_name="testitem", points_spent=10
    )
    assert purchase_log_base.user_id == "testuser"
    assert purchase_log_base.username == "testuser"
    assert purchase_log_base.item_id == "testitem"
    assert purchase_log_base.item_name == "testitem"
    assert purchase_log_base.points_spent == 10
    assert purchase_log_base.status == PurchaseStatus.PENDING


def test_purchase_log_create_model():
    purchase_log_create = PurchaseLogCreate(
        user_id="testuser", username="testuser", item_id="testitem", item_name="testitem", points_spent=10
    )
    assert purchase_log_create.user_id == "testuser"
    assert purchase_log_create.username == "testuser"
    assert purchase_log_create.item_id == "testitem"
    assert purchase_log_create.item_name == "testitem"
    assert purchase_log_create.points_spent == 10


def test_purchase_log_model():
    purchase_log = PurchaseLog(
        id="testlogid",
        user_id="testuser",
        username="testuser",
        item_id="testitem",
        item_name="testitem",
        points_spent=10,
    )
    assert purchase_log.id == "testlogid"
    assert purchase_log.user_id == "testuser"
    assert purchase_log.username == "testuser"
    assert purchase_log.item_id == "testitem"
    assert purchase_log.item_name == "testitem"
    assert purchase_log.points_spent == 10
