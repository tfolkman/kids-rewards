# Assuming main.py, crud.py, models.py, security.py are all in LAMBDA_TASK_ROOT (/var/task)
# and __init__.py makes this directory a package.
# For Lambda containers, often direct imports work if LAMBDA_TASK_ROOT is in sys.path.
import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from mangum import Mangum  # Import Mangum

from . import crud, models, security
from .models import User

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# --- Authentication Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- Dependency to get current user ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = security.decode_access_token(token)
    if username is None:
        raise credentials_exception
    user = crud.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    # We could add a check here for `is_active` if we implement that in the User model
    return current_user


# --- Dependency for Parent-only actions ---
async def get_current_parent_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:
    if current_user.role != models.UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role",
        )
    return current_user


# --- Dependency for Kid-only actions ---
async def get_current_kid_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:
    if current_user.role != models.UserRole.KID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role",
        )
    if current_user.points is None:  # Should always be set for kids, but good to check
        current_user.points = 0  # Initialize if somehow None
    return current_user


app = FastAPI()

# --- CORS Middleware ---
origins = [
    "http://localhost:3000",  # React default dev port
    "http://localhost:3001",  # Frontend dev server port
    "http://localhost:3000",  # Backend server port
    "https://main.dd0mqanef4wnt.amplifyapp.com",  # Deployed Amplify frontend
    # Add other domains here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Endpoints ---

# Lambda handler - Mangum wraps the FastAPI app
# This 'handler' is what AWS Lambda will look for.
handler = Mangum(app)


@app.post("/token", response_model=models.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    user = crud.get_user_by_username(username)
    logger.info(f"Login attempt for user: {username}, User found: {user is not None}")
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    response = {"access_token": access_token, "token_type": "bearer"}
    # headers = {"Access-Control-Allow-Origin": "http://localhost:3001"} # Middleware will handle this
    return response  # FastAPI will handle status and headers correctly with middleware


@app.post("/users/", response_model=models.User, status_code=status.HTTP_201_CREATED)
async def create_user(user: models.UserCreate):
    db_user = crud.get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(user_in=user)


@app.get("/users/me/", response_model=models.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@app.post("/users/promote-to-parent", response_model=models.User)
async def promote_user_to_parent_endpoint(
    promotion_request: models.UserPromoteRequest,
    current_admin_user: models.User = Depends(get_current_parent_user),  # Only parents can promote
):
    user_to_promote = crud.promote_user_to_parent(promotion_request.username)
    if not user_to_promote:
        raise HTTPException(
            status_code=404, detail=f"User {promotion_request.username} not found or could not be promoted."
        )
    return user_to_promote


# --- Points Management Endpoints ---
@app.post("/kids/award-points/", response_model=models.User)
async def award_points_to_kid(
    award: models.PointsAward,
    current_user: models.User = Depends(get_current_parent_user),  # Parent only
):
    kid_user = crud.get_user_by_username(award.kid_username)
    if not kid_user or kid_user.role != models.UserRole.KID:
        raise HTTPException(status_code=404, detail="Kid user not found or user is not a kid")

    updated_kid_user = crud.update_user_points(username=award.kid_username, points_to_add=award.points)
    if not updated_kid_user:
        raise HTTPException(status_code=500, detail="Could not award points")
    return updated_kid_user


@app.post("/kids/redeem-item/", response_model=models.User)
async def redeem_store_item(
    redemption: models.RedemptionRequest,
    current_user: models.User = Depends(get_current_kid_user),  # Kid only
):
    store_item = crud.get_store_item_by_id(redemption.item_id)
    if not store_item:
        raise HTTPException(status_code=404, detail="Store item not found")

    if current_user.points is None or current_user.points < store_item.points_cost:
        raise HTTPException(status_code=400, detail="Not enough points to redeem this item")

    updated_user = crud.update_user_points(username=current_user.username, points_to_add=-store_item.points_cost)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Could not redeem item due to an internal error")
    return updated_user


# --- Store Item Endpoints ---
@app.post("/store/items/", response_model=models.StoreItem, status_code=status.HTTP_201_CREATED)
async def create_store_item(
    item: models.StoreItemCreate,
    current_user: models.User = Depends(get_current_parent_user),  # Parent only
):
    return crud.create_store_item(item_in=item)


@app.get("/store/items/", response_model=list[models.StoreItem])
async def read_store_items(skip: int = 0, limit: int = 100):
    items = crud.get_store_items()
    return items[skip : skip + limit]


@app.get("/store/items/{item_id}", response_model=models.StoreItem)
async def read_store_item(item_id: str):
    db_item = crud.get_store_item_by_id(item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Store item not found")
    return db_item


@app.put("/store/items/{item_id}", response_model=models.StoreItem)
async def update_store_item(
    item_id: str,
    item: models.StoreItemCreate,
    current_user: models.User = Depends(get_current_parent_user),  # Parent only
):
    db_item = crud.update_store_item(item_id=item_id, item_in=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Store item not found")
    return db_item


@app.delete("/store/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store_item(
    item_id: str,
    current_user: models.User = Depends(get_current_parent_user),  # Parent only
):
    success = crud.delete_store_item(item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Store item not found")
    return None


@app.get("/")
async def read_root():
    return {"message": "Kids Rewards API is running!"}


@app.get("/leaderboard", response_model=list[User])
async def get_leaderboard():
    """Get all users sorted by points (highest to lowest)"""
    users = crud.get_all_users()
    # Sort users by points (descending), putting users with None points at the end
    sorted_users = sorted(users, key=lambda u: u.points if u.points is not None else -1, reverse=True)
    return sorted_users


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/hello")
async def hello_world():
    response = {"message": "Hello, world!"}
    # headers = {"Access-Control-Allow-Origin": "http://localhost:3001"} # Middleware will handle this
    return response  # FastAPI will handle status and headers correctly with middleware
