# Assuming main.py, crud.py, models.py, security.py are all in LAMBDA_TASK_ROOT (/var/task)
# and __init__.py makes this directory a package.
# For Lambda containers, often direct imports work if LAMBDA_TASK_ROOT is in sys.path.
import asyncio
import logging
import os
from datetime import timedelta
from typing import List, Optional  # noqa: UP035

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import Depends, FastAPI, Header, HTTPException, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # noqa: E402
from mangum import Mangum  # Import Mangum # noqa: E402

import care_guide  # noqa: E402
import crud  # noqa: E402
import models  # noqa: E402
import security  # noqa: E402
from models import User  # noqa: E402

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


async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:  # noqa: B008
    # We could add a check here for `is_active` if we implement that in the User model
    return current_user


# --- Dependency for Parent-only actions ---
async def get_current_parent_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:  # noqa: B008
    if current_user.role != models.UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role",
        )
    return current_user


# --- Dependency for Kid-only actions ---
async def get_current_kid_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:  # noqa: B008
    if current_user.role != models.UserRole.KID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role",
        )
    if current_user.points is None:  # Should always be set for kids, but good to check
        current_user.points = 0  # Initialize if somehow None
    return current_user


async def verify_home_assistant_api_key(x_ha_api_key: Optional[str] = Header(None)) -> bool:
    """Verify Home Assistant API key"""
    if not x_ha_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-HA-API-Key header")
    if not security.verify_ha_api_key(x_ha_api_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
    return True


app = FastAPI()

# --- CORS Middleware ---
origins = [
    "http://localhost:3000",  # React default dev port
    "http://localhost:3001",  # Frontend dev server port
    "http://localhost:3000",  # Backend server port
    "https://main.dd0mqanef4wnt.amplifyapp.com",
    "https://monkeypoints.shop",
    "https://www.monkeypoints.shop",  # Deployed Amplify frontend
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
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):  # noqa: B008
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
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):  # noqa: B008
    return current_user


@app.post("/users/promote-to-parent", response_model=models.User)
async def promote_user_to_parent_endpoint(promotion_request: models.UserPromoteRequest):
    user_to_promote = crud.promote_user_to_parent(promotion_request.username)
    if not user_to_promote:
        raise HTTPException(
            status_code=404, detail=f"User {promotion_request.username} not found or could not be promoted."
        )
    return user_to_promote


# --- Points Management Endpoints ---
@app.post("/kids/award-points/", response_model=models.User)
async def award_points_to_kid(award: models.PointsAward):
    kid_user = crud.get_user_by_username(award.kid_username)
    if not kid_user or kid_user.role != models.UserRole.KID:
        raise HTTPException(status_code=404, detail="Kid user not found or user is not a kid")

    updated_kid_user = crud.update_user_points(username=award.kid_username, points_to_add=award.points)
    if not updated_kid_user:
        raise HTTPException(status_code=500, detail="Could not award points")
    return updated_kid_user


@app.post(
    "/kids/redeem-item/", response_model=models.PurchaseLog, status_code=status.HTTP_202_ACCEPTED
)  # Changed response model and status
async def request_redeem_store_item(  # Renamed function for clarity
    redemption: models.RedemptionRequest,
    current_user: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    store_item = crud.get_store_item_by_id(redemption.item_id)
    if not store_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store item not found")

    # Check if user has enough points at the time of request
    if current_user.points is None or current_user.points < store_item.points_cost:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough points to request this item")

    # Create a purchase log with PENDING status. Points are NOT deducted yet.
    try:
        purchase_log_entry = models.PurchaseLogCreate(
            user_id=current_user.id,
            username=current_user.username,
            item_id=store_item.id,
            item_name=store_item.name,
            points_spent=store_item.points_cost,
            # status will default to PENDING as per the model
        )
        created_log = crud.create_purchase_log(purchase_log_entry)
        return created_log  # Return the created log entry
    except Exception as e:
        print(f"Error creating PENDING purchase log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create purchase request."
        ) from e


# --- Store Item Endpoints ---
@app.post("/store/items/", response_model=models.StoreItem, status_code=status.HTTP_201_CREATED)
async def create_store_item(item: models.StoreItemCreate):
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
async def update_store_item(item_id: str, item: models.StoreItemCreate):
    db_item = crud.update_store_item(item_id=item_id, item_in=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Store item not found")
    return db_item


@app.delete("/store/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store_item(item_id: str):
    success = crud.delete_store_item(item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Store item not found")
    return None


# --- Chore Management Endpoints (Parent) ---


@app.post("/chores/", response_model=models.Chore, status_code=status.HTTP_201_CREATED)
async def create_new_chore(
    chore_in: models.ChoreCreate,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Create a new chore. Only accessible by parents.
    The `created_by_parent_id` will be the ID of the authenticated parent.
    """
    return crud.create_chore(chore_in=chore_in, parent_id=current_parent.id)


@app.get("/chores/my-chores/", response_model=List[models.Chore])  # noqa: UP006
async def get_my_created_chores(
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Get all chores created by the currently authenticated parent.
    """
    # This assumes a GSI 'ParentChoresIndex' on chores_table or a scan fallback in crud
    return crud.get_chores_by_parent(parent_id=current_parent.id)


@app.put("/chores/{chore_id}", response_model=models.Chore)
async def update_existing_chore(
    chore_id: str,
    chore_in: models.ChoreCreate,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Update an existing chore. Only the parent who created the chore can update it.
    """
    updated_chore = crud.update_chore(chore_id=chore_id, chore_in=chore_in, current_parent_id=current_parent.id)
    if not updated_chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chore not found or not authorized to update."
        )
    return updated_chore


@app.post("/chores/{chore_id}/deactivate", response_model=models.Chore)
async def deactivate_existing_chore(
    chore_id: str,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Deactivate a chore. Only the parent who created it can deactivate.
    """
    deactivated_chore = crud.deactivate_chore(chore_id=chore_id, current_parent_id=current_parent.id)
    if not deactivated_chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chore not found or not authorized to deactivate."
        )
    return deactivated_chore


@app.delete("/chores/{chore_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_chore(
    chore_id: str,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Delete a chore. Only the parent who created it can delete.
    Consider implications for existing chore logs.
    """
    success = crud.delete_chore(chore_id=chore_id, current_parent_id=current_parent.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chore not found or not authorized to delete."
        )
    return None


# --- Chore Interaction Endpoints (Kid & General) ---


@app.get("/chores/", response_model=List[models.Chore])  # noqa: UP006
async def get_available_chores():
    """
    Get all active and available chores.
    """
    return crud.get_all_active_chores()


@app.get("/chores/{chore_id}", response_model=models.Chore)
async def get_specific_chore(chore_id: str):
    """
    Get details of a specific chore by its ID.
    """
    chore = crud.get_chore_by_id(chore_id)
    if not chore:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chore not found.")
    return chore


@app.post("/chores/{chore_id}/submit", response_model=models.ChoreLog, status_code=status.HTTP_202_ACCEPTED)
async def submit_chore_completion(
    chore_id: str,
    submission: models.ChoreSubmission,
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid submits a chore they have completed. Creates a ChoreLog entry with PENDING_APPROVAL status.

    Now includes effort tracking features:
    - effort_minutes: Time spent working on the chore (0-240 minutes)
    - effort_points: Calculated as 0.5 points per minute, max 10 points
    - retry_count: Number of previous attempts in last 24 hours
    - is_retry: Whether this is a retry of a previously rejected/pending chore

    Effort points contribute to streaks even if the chore is rejected (if >= 10 minutes).
    This encourages persistence and rewards effort over just outcomes.
    """
    chore_log = crud.create_chore_log_submission(
        chore_id=chore_id, kid_user=current_kid, effort_minutes=submission.effort_minutes
    )
    if not chore_log:
        # crud function raises HTTPException, so this might be redundant
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not submit chore completion."
        )
    return chore_log


@app.get("/chores/history/me", response_model=List[models.ChoreLog])  # noqa: UP006
async def get_my_chore_history(
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid retrieves their own chore history.
    """
    # Assumes GSI 'KidChoreLogIndex' or scan fallback in crud
    return crud.get_chore_logs_by_kid_id(kid_id=current_kid.id)


class ChoreLogWithStreakBonus(models.ChoreLog):
    """Extended ChoreLog model that includes streak bonus information"""

    streak_bonus_points: Optional[int] = None
    streak_day: Optional[int] = None


@app.get("/chores/history/me/detailed", response_model=List[ChoreLogWithStreakBonus])  # noqa: UP006
async def get_my_detailed_chore_history(
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid retrieves their own chore history with streak bonus information.
    """
    chore_logs = crud.get_chore_logs_by_kid_id(kid_id=current_kid.id)

    # Filter for approved chores and sort by date
    approved_logs = [log for log in chore_logs if log.status == models.ChoreStatus.APPROVED]
    approved_logs.sort(key=lambda x: x.submitted_at)

    # Track which dates have been processed and current streak
    processed_dates = set()
    streak_milestones = {3: 10, 7: 25, 14: 50, 30: 100}
    detailed_logs = []
    current_streak = 0
    last_date = None

    for log in approved_logs:
        log_date = log.submitted_at.date()
        log_dict = log.dict()

        # Check if this is a new day
        if log_date not in processed_dates:
            processed_dates.add(log_date)

            # Check if streak continues or breaks
            if last_date is None:
                current_streak = 1
            elif (log_date - last_date).days == 1:
                current_streak += 1
            elif (log_date - last_date).days > 1:
                current_streak = 1

            # Check if this day hits a milestone
            if current_streak in streak_milestones:
                log_dict["streak_bonus_points"] = streak_milestones[current_streak]
                log_dict["streak_day"] = current_streak
            else:
                log_dict["streak_bonus_points"] = None
                log_dict["streak_day"] = current_streak

            last_date = log_date
        else:
            # Same day, no streak bonus
            log_dict["streak_bonus_points"] = None
            log_dict["streak_day"] = None

        detailed_logs.append(ChoreLogWithStreakBonus(**log_dict))

    # Sort by date descending (newest first) for display
    detailed_logs.sort(key=lambda x: x.submitted_at, reverse=True)

    return detailed_logs


# --- Chore Approval Endpoints (Parent) ---


class ChoreActionRequest(models.BaseModel):
    chore_log_id: str


@app.get("/parent/chore-submissions/pending", response_model=List[models.ChoreLog])  # noqa: UP006
async def get_pending_chore_submissions_for_my_chores(
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent retrieves all PENDING chore submissions for chores they originally created.
    """
    # This assumes a GSI or complex filtering in crud.get_chore_logs_by_status_for_parent
    return crud.get_chore_logs_by_status_for_parent(
        status=models.ChoreStatus.PENDING_APPROVAL, parent_id=current_parent.id
    )


@app.post("/parent/chore-submissions/approve", response_model=models.ChoreLog)
async def approve_chore_submission(
    request_data: ChoreActionRequest,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent approves a chore submission. Points are awarded to the kid.
    Only the parent who created the original chore can approve.
    """
    # crud.update_chore_log_status handles logic including point awarding and authorization
    approved_log = crud.update_chore_log_status(
        log_id=request_data.chore_log_id, new_status=models.ChoreStatus.APPROVED, parent_user=current_parent
    )
    if not approved_log:
        # crud function raises detailed HTTPExceptions, this is a fallback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve chore submission."
        )
    return approved_log


@app.post("/parent/chore-submissions/reject", response_model=models.ChoreLog)
async def reject_chore_submission(
    request_data: ChoreActionRequest,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent rejects a chore submission.
    Only the parent who created the original chore can reject.
    """
    rejected_log = crud.update_chore_log_status(
        log_id=request_data.chore_log_id, new_status=models.ChoreStatus.REJECTED, parent_user=current_parent
    )
    if not rejected_log:
        # crud function raises detailed HTTPExceptions, this is a fallback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject chore submission."
        )
    return rejected_log


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


@app.get("/api/home-assistant/pet-tasks/today", response_model=models.HomeAssistantTasksResponse)
async def get_todays_pet_tasks_for_home_assistant(
    authorized: bool = Depends(verify_home_assistant_api_key),  # noqa: B008, ARG001
):
    """
    Get today's pet care tasks for Home Assistant.
    Requires X-HA-API-Key header.
    """
    from datetime import date, datetime, time

    # Get today's date range
    today = date.today()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)

    # Get all tasks and filter for today
    all_tasks = crud.get_all_pet_care_tasks()
    todays_tasks = [task for task in all_tasks if today_start <= task.due_date <= today_end]

    # Transform to HA-friendly format
    ha_tasks = []
    for task in todays_tasks:
        # Map status
        if task.status == models.PetCareTaskStatus.APPROVED:
            status_str = "done"
        elif task.status == models.PetCareTaskStatus.PENDING_APPROVAL:
            status_str = "awaiting_approval"
        else:
            status_str = "pending"

        # Check overdue
        is_overdue = task.due_date < datetime.now() and task.status != models.PetCareTaskStatus.APPROVED

        ha_tasks.append(
            models.HomeAssistantPetTask(
                pet_name=task.pet_name,
                task_name=task.task_name,
                assigned_to=task.assigned_to_kid_username,
                due_time=task.due_date.strftime("%H:%M"),
                status=status_str,
                points=task.points_value,
                is_overdue=is_overdue,
            )
        )

    # Summary
    summary = {
        "total": len(ha_tasks),
        "done": sum(1 for t in ha_tasks if t.status == "done"),
        "pending": sum(1 for t in ha_tasks if t.status == "pending"),
        "awaiting_approval": sum(1 for t in ha_tasks if t.status == "awaiting_approval"),
        "overdue": sum(1 for t in ha_tasks if t.is_overdue),
    }

    return models.HomeAssistantTasksResponse(today=today.isoformat(), tasks=ha_tasks, summary=summary)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/hello")
async def hello_world():
    response = {"message": "Hello, world!"}
    # headers = {"Access-Control-Allow-Origin": "http://localhost:3001"} # Middleware will handle this
    return response  # FastAPI will handle status and headers correctly with middleware


@app.get("/users/me/purchase-history", response_model=List[models.PurchaseLog])  # noqa: UP006
async def read_my_purchase_history(current_user: models.User = Depends(get_current_active_user)):  # noqa: B008
    """
    Retrieve the purchase history for the currently authenticated user.
    """
    # Uses the GSI 'UserIdTimestampIndex' if available, otherwise falls back to scan.
    # Sorted by timestamp descending (newest first) by default in crud.get_purchase_logs_by_user_id
    # or by client-side sort in get_all_purchase_logs fallback.
    history = crud.get_purchase_logs_by_user_id(user_id=current_user.id)
    return history


@app.get("/kids/bearded-dragon-purchases", response_model=List[models.PurchaseLog])  # noqa: UP006
async def get_bearded_dragon_purchases(current_user: models.User = Depends(get_current_active_user)):  # noqa: B008
    """
    Retrieve all bearded dragon item purchases for all three kids (Clara, Emery, Aiden).
    Accessible to both kids and parents for tracking collective goal progress.
    """
    BEARDED_DRAGON_ITEM_ID = "4d35256f-f226-43d7-8211-627891059ebf"

    logger.info(f"Bearded dragon purchases requested by {current_user.username}")

    # Get all purchase logs from the system
    all_purchases = crud.get_all_purchase_logs()

    # Filter for bearded dragon purchases from the three kids
    valid_usernames = ["clara", "emery", "aiden"]
    bearded_dragon_purchases = [
        purchase
        for purchase in all_purchases
        if purchase.item_id == BEARDED_DRAGON_ITEM_ID and purchase.username.lower() in valid_usernames
    ]

    # Sort by timestamp descending (newest first)
    bearded_dragon_purchases.sort(key=lambda x: x.timestamp, reverse=True)

    logger.info(f"Found {len(bearded_dragon_purchases)} bearded dragon purchases for collective goal")

    return bearded_dragon_purchases


# --- Gemini API Endpoint ---
import google.generativeai as genai  # noqa: E402
from pydantic import BaseModel  # noqa: E402


class GeminiRequest(BaseModel):
    prompt: str
    question: str


class GeminiResponse(BaseModel):
    answer: str


GEMINI_API_KEY = "AIzaSyDxtt9DIaj9Gvp1MGxwKEa4aTyfV0XG5lM"


@app.post("/gemini/ask", response_model=GeminiResponse)
async def ask_gemini(request: GeminiRequest):
    logger.info("Received request to ask Gemini")
    try:
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API key is not set.")
        os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        # Combine prompt and question
        full_request = f"{request.prompt}\n\n{request.question}"

        logger.info(f"Asking Gemini: {full_request}")
        response = model.generate_content(full_request)
        logger.info(f"Gemini response: {response.text}")
        return GeminiResponse(answer=response.text)
    except Exception as e:
        logger.error(f"Error asking Gemini: {type(e).__name__}: {e}")
        return GeminiResponse(answer=f"Error: {type(e).__name__}: {e}")


async def test_gemini_api():
    try:
        # Hardcoding API key for testing purposes
        test_api_key = "AIzaSyDxtt9DIaj9Gvp1MGxwKEa4aTyfV0XG5lM"
        if not test_api_key:
            print("Gemini API key is not set.")
            return
        os.environ["GOOGLE_API_KEY"] = test_api_key
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        test_question = "What is the capital of France?"
        print(f"Asking Gemini (test): {test_question}")
        response = model.generate_content(test_question)
        print(f"Gemini response (test): {response.text}")
    except Exception as e:
        print(f"Error during Gemini API test: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_gemini_api())


async def test_gemini_api():
    try:
        if not GEMINI_API_KEY:
            print("Gemini API key is not set.")
            return
        os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        model = genai.GenerativeModel("gemini-pro")
        test_question = "What is the capital of France?"
        print(f"Asking Gemini (test): {test_question}")
        response = model.generate_content(test_question)
        print(f"Gemini response (test): {response.text}")
    except Exception as e:
        print(f"Error during Gemini API test: {type(e).__name__}: {e}")


# --- Purchase Approval Endpoints (Parent Only) ---


class PurchaseActionRequest(models.BaseModel):
    log_id: str


@app.get("/parent/purchase-requests/pending", response_model=List[models.PurchaseLog])  # noqa: UP006
async def get_pending_purchase_requests():
    """
    Retrieve all purchase requests with 'pending' status.
    Sorted by timestamp descending (newest first).
    """
    pending_logs = crud.get_purchase_logs_by_status(models.PurchaseStatus.PENDING)
    return pending_logs


@app.post("/parent/purchase-requests/approve", response_model=models.PurchaseLog)
async def approve_purchase_request(request_data: PurchaseActionRequest):
    log_to_approve = crud.get_purchase_log_by_id(request_data.log_id)  # Assumes get_purchase_log_by_id exists

    if not log_to_approve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase log not found.")
    if log_to_approve.status != models.PurchaseStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase request is not pending.")

    kid_user = crud.get_user_by_username(log_to_approve.username)
    if not kid_user or kid_user.role != models.UserRole.KID:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kid user associated with the purchase not found."
        )

    if kid_user.points is None or kid_user.points < log_to_approve.points_spent:
        # Optionally, could reject automatically or just inform parent
        updated_log_insufficient_points = crud.update_purchase_log_status(
            log_to_approve.id, models.PurchaseStatus.REJECTED
        )
        if not updated_log_insufficient_points:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update log status for insufficient points.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kid {kid_user.username} no longer has enough points. Request auto-rejected.",
        )

    # Deduct points
    updated_kid = crud.update_user_points(username=kid_user.username, points_to_add=-log_to_approve.points_spent)
    if not updated_kid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to deduct points from kid."
        )

    # Update log status to APPROVED
    approved_log = crud.update_purchase_log_status(log_to_approve.id, models.PurchaseStatus.APPROVED)
    if not approved_log:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update purchase log status to approved.",
        )

    return approved_log


@app.post("/parent/purchase-requests/reject", response_model=models.PurchaseLog)
async def reject_purchase_request(request_data: PurchaseActionRequest):
    log_to_reject = crud.get_purchase_log_by_id(request_data.log_id)  # Assumes get_purchase_log_by_id exists

    if not log_to_reject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase log not found.")
    if log_to_reject.status != models.PurchaseStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase request is not pending.")

    rejected_log = crud.update_purchase_log_status(log_to_reject.id, models.PurchaseStatus.REJECTED)
    if not rejected_log:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update purchase log status to rejected.",
        )

    return rejected_log


# --- Feature Request Endpoints ---


class KidFeatureRequestPayload(models.BaseModel):
    request_type: models.RequestType
    details: dict  # Specifics of the request, e.g., {"name": "New Item", "points_cost": 100}


@app.post("/requests/", response_model=models.Request, status_code=status.HTTP_201_CREATED)
async def create_feature_request(
    payload: KidFeatureRequestPayload,
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid creates a new feature request (e.g., add store item, add chore, other).
    """
    logger.info(
        f"User {current_kid.username} (ID: {current_kid.id}) creating feature request of type {payload.request_type.value} with details: {payload.details}"
    )
    request_create_data = models.RequestCreate(
        requester_id=current_kid.id,
        requester_username=current_kid.username,
        request_type=payload.request_type,
        details=payload.details,
        # status defaults to PENDING in RequestBase model
    )
    created_request = crud.create_request(request_in=request_create_data)
    if not created_request:
        logger.error(f"Failed to create feature request for user {current_kid.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create feature request."
        )
    logger.info(f"Feature request {created_request.id} created successfully for user {current_kid.username}")
    return created_request


@app.get("/requests/me/", response_model=List[models.Request])  # noqa: UP006
async def get_my_feature_requests(
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid retrieves their own submitted feature requests.
    """
    logger.info(f"Fetching feature requests for user {current_kid.username} (ID: {current_kid.id})")
    requests = crud.get_requests_by_requester_id(requester_id=current_kid.id)
    logger.info(f"Found {len(requests)} feature requests for user {current_kid.username}")
    return requests


@app.get("/parent/requests/pending/", response_model=List[models.Request])  # noqa: UP006
async def get_pending_feature_requests(
    current_parent: models.User = Depends(get_current_parent_user),  # Ensures only parents can access # noqa: B008
):
    """
    Parent retrieves all feature requests with 'pending' status.
    """
    logger.info(f"Parent {current_parent.username} fetching pending feature requests.")
    pending_requests = crud.get_requests_by_status(status=models.RequestStatus.PENDING)
    logger.info(f"Found {len(pending_requests)} pending feature requests.")
    return pending_requests


@app.post("/parent/requests/{request_id}/approve/", response_model=models.Request)
async def approve_feature_request(
    request_id: str,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent approves a feature request.
    If the request type is ADD_STORE_ITEM or ADD_CHORE, the item/chore is created.
    """
    logger.info(f"Parent {current_parent.username} attempting to approve request {request_id}")
    updated_request = crud.update_request_status(
        request_id=request_id, new_status=models.RequestStatus.APPROVED, parent_id=current_parent.id
    )
    if not updated_request:
        logger.warning(
            f"Failed to approve request {request_id} by parent {current_parent.username}. Request not found or update failed."
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or could not be approved.")
    logger.info(
        f"Request {request_id} approved successfully by parent {current_parent.username}. New status: {updated_request.status.value}"
    )
    return updated_request


@app.post("/parent/requests/{request_id}/reject/", response_model=models.Request)
async def reject_feature_request(
    request_id: str,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent rejects a feature request.
    """
    logger.info(f"Parent {current_parent.username} attempting to reject request {request_id}")
    updated_request = crud.update_request_status(
        request_id=request_id, new_status=models.RequestStatus.REJECTED, parent_id=current_parent.id
    )
    if not updated_request:
        logger.warning(
            f"Failed to reject request {request_id} by parent {current_parent.username}. Request not found or update failed."
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or could not be rejected.")
    logger.info(
        f"Request {request_id} rejected successfully by parent {current_parent.username}. New status: {updated_request.status.value}"
    )
    return updated_request


# --- Chore Assignment Endpoints ---


# Data models for API requests
class ChoreAssignmentRequest(models.BaseModel):
    chore_id: str
    assigned_to_kid_id: str  # Kid's username
    due_date: str  # ISO date string
    notes: Optional[str] = None


class ChoreAssignmentActionRequest(models.BaseModel):
    assignment_id: str


# Parent - Assign chore to kid
@app.post("/parent/chore-assignments/", response_model=models.ChoreAssignment, status_code=status.HTTP_201_CREATED)
async def assign_chore_to_kid(
    assignment_request: ChoreAssignmentRequest,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent assigns a chore to a specific kid with a due date.
    """
    try:
        # Parse the due date
        from datetime import datetime

        due_date = datetime.fromisoformat(assignment_request.due_date.replace("Z", "+00:00"))

        assignment_create = models.ChoreAssignmentCreate(
            chore_id=assignment_request.chore_id,
            assigned_to_kid_id=assignment_request.assigned_to_kid_id,
            due_date=due_date,
            notes=assignment_request.notes,
        )

        return crud.create_chore_assignment(assignment_in=assignment_create, parent_id=current_parent.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid due date format: {e}")


# Kid - Get assigned chores
@app.get("/kids/my-assignments/", response_model=List[models.ChoreAssignment])  # noqa: UP006
async def get_my_assigned_chores(
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid retrieves their assigned chores.
    """
    return crud.get_assignments_by_kid_id(kid_id=current_kid.username)


# Kid - Get streak data
@app.get("/kids/streak/", response_model=dict)
async def get_my_streak(
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid retrieves their current streak information.
    """
    logger.info(f"Fetching streak data for kid {current_kid.username}")
    streak_data = crud.calculate_streak_for_kid(kid_id=current_kid.username)
    logger.info(f"Streak data for {current_kid.username}: {streak_data}")
    return streak_data


# Kid - Submit assignment completion
@app.post(
    "/chore-assignments/{assignment_id}/submit",
    response_model=models.ChoreAssignment,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_assignment_completion(
    assignment_id: str,
    submission_data: models.ChoreAssignmentSubmission,
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid submits completion of an assigned chore.
    """
    assignment = crud.submit_assignment_completion(
        assignment_id=assignment_id, kid_user=current_kid, submission_notes=submission_data.submission_notes
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not submit assignment completion."
        )
    return assignment


# Parent - Get pending assignment submissions
@app.get("/parent/assignment-submissions/pending", response_model=List[models.ChoreAssignment])  # noqa: UP006
async def get_pending_assignment_submissions_for_my_assignments(
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent retrieves all SUBMITTED assignment submissions for assignments they created.
    """
    return crud.get_assignments_by_status_for_parent(
        status=models.ChoreAssignmentStatus.SUBMITTED, parent_id=current_parent.id
    )


# Parent - Approve assignment submission
@app.post("/parent/assignment-submissions/approve", response_model=models.ChoreAssignment)
async def approve_assignment_submission(
    request_data: ChoreAssignmentActionRequest,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent approves an assignment submission. Points are awarded to the kid.
    Only the parent who created the assignment can approve.
    """
    approved_assignment = crud.update_assignment_status(
        assignment_id=request_data.assignment_id,
        new_status=models.ChoreAssignmentStatus.APPROVED,
        parent_user=current_parent,
    )
    if not approved_assignment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve assignment submission."
        )
    return approved_assignment


# Parent - Reject assignment submission
@app.post("/parent/assignment-submissions/reject", response_model=models.ChoreAssignment)
async def reject_assignment_submission(
    request_data: ChoreAssignmentActionRequest,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent rejects an assignment submission.
    Only the parent who created the assignment can reject.
    """
    rejected_assignment = crud.update_assignment_status(
        assignment_id=request_data.assignment_id,
        new_status=models.ChoreAssignmentStatus.REJECTED,
        parent_user=current_parent,
    )
    if not rejected_assignment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject assignment submission."
        )
    return rejected_assignment


# Parent - Get all assignments (for management)
@app.get("/parent/chore-assignments/", response_model=List[models.ChoreAssignment])  # noqa: UP006
async def get_my_chore_assignments(
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """
    Parent retrieves all chore assignments they have created.
    """
    return crud.get_assignments_by_parent_id(parent_id=current_parent.id)


# --- Pet Care Endpoints ---

import pet_care  # noqa: E402


# Pet CRUD - Parent only
@app.post("/pets/", response_model=models.PetWithAge, status_code=status.HTTP_201_CREATED)
async def create_pet(
    pet_in: models.PetCreate,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Create a new pet. Only accessible by parents."""
    pet = crud.create_pet(pet_in=pet_in, parent_id=current_parent.id)
    return pet_care.get_pet_with_age(pet)


@app.get("/pets/", response_model=List[models.PetWithAge])  # noqa: UP006
async def get_pets(
    current_user: models.User = Depends(get_current_active_user),  # noqa: B008
):
    """Get all active pets. Accessible to all authenticated users."""
    pets = crud.get_active_pets()
    return [pet_care.get_pet_with_age(pet) for pet in pets]


@app.get("/pets/{pet_id}", response_model=models.PetWithAge)
async def get_pet(
    pet_id: str,
    current_user: models.User = Depends(get_current_active_user),  # noqa: B008
):
    """Get a specific pet by ID."""
    pet = crud.get_pet_by_id(pet_id)
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")
    return pet_care.get_pet_with_age(pet)


@app.get("/pets/{pet_id}/care-recommendations", response_model=models.CareRecommendation)
async def get_pet_care_recommendations(
    pet_id: str,
    current_user: models.User = Depends(get_current_active_user),  # noqa: B008
):
    """Get age-appropriate care recommendations for a pet."""
    pet = crud.get_pet_by_id(pet_id)
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")
    pet_with_age = pet_care.get_pet_with_age(pet)
    return pet_care.get_care_recommendations(pet.species, pet_with_age.life_stage)


@app.get("/pets/{pet_id}/recommended-schedules", response_model=List[models.RecommendedCareSchedule])  # noqa: UP006
async def get_recommended_schedules(
    pet_id: str,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Get recommended care schedules for a pet based on its species and life stage."""
    pet = crud.get_pet_by_id(pet_id)
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")
    pet_with_age = pet_care.get_pet_with_age(pet)
    life_stage = care_guide.LifeStage(pet_with_age.life_stage.value)
    schedules = care_guide.get_recommended_schedules(pet.species.value, life_stage)
    return [
        models.RecommendedCareSchedule(
            task_name=s["task_name"],
            task_type=s["task_type"].value,
            frequency=models.CareFrequency(s["frequency"])
            if s["frequency"] in ["daily", "weekly"]
            else models.CareFrequency.DAILY,
            points_value=s["points_value"],
            description=s["description"],
        )
        for s in schedules
    ]


@app.put("/pets/{pet_id}", response_model=models.PetWithAge)
async def update_pet(
    pet_id: str,
    pet_in: models.PetCreate,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Update a pet. Only the parent who created the pet can update it."""
    updated_pet = crud.update_pet(pet_id=pet_id, pet_in=pet_in, parent_id=current_parent.id)
    if not updated_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found or not authorized to update.")
    return pet_care.get_pet_with_age(updated_pet)


@app.post("/pets/{pet_id}/deactivate", response_model=models.PetWithAge)
async def deactivate_pet(
    pet_id: str,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Deactivate a pet. Only the parent who created the pet can deactivate it."""
    deactivated_pet = crud.deactivate_pet(pet_id=pet_id, parent_id=current_parent.id)
    if not deactivated_pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found or not authorized to deactivate."
        )
    return pet_care.get_pet_with_age(deactivated_pet)


# Pet Care Schedule CRUD - Parent only
@app.post("/pets/schedules/", response_model=models.PetCareSchedule, status_code=status.HTTP_201_CREATED)
async def create_pet_care_schedule(
    schedule_in: models.PetCareScheduleCreate,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Create a new pet care schedule. Only accessible by parents."""
    return crud.create_pet_care_schedule(schedule_in=schedule_in, parent_id=current_parent.id)


@app.get("/pets/{pet_id}/schedules/", response_model=List[models.PetCareSchedule])  # noqa: UP006
async def get_pet_schedules(
    pet_id: str,
    current_user: models.User = Depends(get_current_active_user),  # noqa: B008
):
    """Get all care schedules for a pet."""
    return crud.get_schedules_by_pet_id(pet_id)


@app.post("/pets/schedules/{schedule_id}/deactivate", response_model=models.PetCareSchedule)
async def deactivate_pet_care_schedule(
    schedule_id: str,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Deactivate a pet care schedule. Only the parent who created it can deactivate."""
    deactivated_schedule = crud.deactivate_schedule(schedule_id=schedule_id, parent_id=current_parent.id)
    if not deactivated_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found or not authorized to deactivate."
        )
    return deactivated_schedule


@app.post("/pets/schedules/{schedule_id}/generate-tasks", response_model=List[models.PetCareTask])  # noqa: UP006
async def generate_pet_care_tasks(
    schedule_id: str,
    days_ahead: int = 7,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Generate pet care tasks from a schedule for the next N days."""
    schedule = crud.get_schedule_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found.")
    if schedule.parent_id != current_parent.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

    pet = crud.get_pet_by_id(schedule.pet_id)
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    # Get kid usernames for rotation
    kid_usernames = {}
    for kid_id in schedule.assigned_kid_ids:
        user = crud.get_user_by_username(kid_id)
        if user:
            kid_usernames[kid_id] = user.username

    # Get existing task dates to avoid duplicates
    existing_tasks = crud.get_tasks_by_pet_id(pet.id)
    existing_task_dates = {
        task.due_date.date().isoformat() for task in existing_tasks if task.schedule_id == schedule_id
    }

    # Generate tasks
    task_creates = pet_care.generate_tasks_for_schedule(
        schedule, pet, kid_usernames, days_ahead=days_ahead, existing_task_dates=existing_task_dates
    )

    # Create tasks in database
    created_tasks = []
    for task_create in task_creates:
        task = crud.create_pet_care_task(task_create)
        created_tasks.append(task)

    # Update rotation index
    if created_tasks:
        new_index = (schedule.rotation_index + len(created_tasks)) % len(schedule.assigned_kid_ids)
        crud.update_schedule_rotation_index(schedule_id, new_index)

    return created_tasks


# Pet Care Tasks - Kid and Parent
@app.get("/kids/my-pet-tasks/", response_model=List[models.PetCareTask])  # noqa: UP006
async def get_my_pet_tasks(
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """Kid retrieves their assigned pet care tasks."""
    return crud.get_tasks_by_kid_id(kid_id=current_kid.username)


@app.get("/pets/{pet_id}/tasks/", response_model=List[models.PetCareTask])  # noqa: UP006
async def get_pet_tasks(
    pet_id: str,
    current_user: models.User = Depends(get_current_active_user),  # noqa: B008
):
    """Get all care tasks for a pet."""
    return crud.get_tasks_by_pet_id(pet_id)


@app.post(
    "/pets/tasks/{task_id}/submit",
    response_model=models.PetCareTask,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_pet_care_task(
    task_id: str,
    submission: models.PetCareTaskSubmission,
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """Kid submits completion of a pet care task."""
    task = crud.submit_pet_care_task(task_id=task_id, kid_user=current_kid, notes=submission.notes)
    if not task:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not submit pet care task.")
    return task


@app.get("/parent/pet-task-submissions/pending", response_model=List[models.PetCareTask])  # noqa: UP006
async def get_pending_pet_task_submissions(
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Parent retrieves all pending pet care task submissions."""
    pending_tasks = crud.get_tasks_by_status(models.PetCareTaskStatus.PENDING_APPROVAL)
    # Filter to only tasks for pets the parent owns
    parent_pets = crud.get_pets_by_parent_id(current_parent.id)
    parent_pet_ids = {pet.id for pet in parent_pets}
    return [task for task in pending_tasks if task.pet_id in parent_pet_ids]


class PetCareTaskActionRequest(models.BaseModel):
    task_id: str


@app.post("/parent/pet-task-submissions/approve", response_model=models.PetCareTask)
async def approve_pet_care_task_submission(
    request_data: PetCareTaskActionRequest,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Parent approves a pet care task submission. Points are awarded to the kid."""
    approved_task = crud.update_pet_care_task_status(
        task_id=request_data.task_id,
        new_status=models.PetCareTaskStatus.APPROVED,
        parent_user=current_parent,
    )
    if not approved_task:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve pet care task."
        )
    return approved_task


@app.post("/parent/pet-task-submissions/reject", response_model=models.PetCareTask)
async def reject_pet_care_task_submission(
    request_data: PetCareTaskActionRequest,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Parent rejects a pet care task submission."""
    rejected_task = crud.update_pet_care_task_status(
        task_id=request_data.task_id,
        new_status=models.PetCareTaskStatus.REJECTED,
        parent_user=current_parent,
    )
    if not rejected_task:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject pet care task.")
    return rejected_task


# Pet Health Logs
@app.post("/pets/{pet_id}/health-logs/", response_model=models.PetHealthLog, status_code=status.HTTP_201_CREATED)
async def create_pet_health_log(
    pet_id: str,
    log_in: models.PetHealthLogCreate,
    current_user: models.User = Depends(get_current_active_user),  # noqa: B008
):
    """Create a health log entry for a pet. Any authenticated user can log."""
    if log_in.pet_id != pet_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pet ID mismatch.")
    return crud.create_pet_health_log(log_in=log_in, user=current_user)


@app.get("/pets/{pet_id}/health-logs/", response_model=List[models.PetHealthLog])  # noqa: UP006
async def get_pet_health_logs(
    pet_id: str,
    current_user: models.User = Depends(get_current_active_user),  # noqa: B008
):
    """Get all health logs for a pet, ordered by most recent first."""
    return crud.get_health_logs_by_pet_id(pet_id)


# Pet Care Overview
@app.get("/pets/overview/", response_model=dict)
async def get_pet_care_overview(
    current_user: models.User = Depends(get_current_active_user),  # noqa: B008
):
    """Get an overview of all pets with their current status and upcoming tasks."""
    pets = crud.get_active_pets()
    overview = []

    for pet in pets:
        pet_with_age = pet_care.get_pet_with_age(pet)
        care_rec = pet_care.get_care_recommendations(pet.species, pet_with_age.life_stage)
        tasks = crud.get_tasks_by_pet_id(pet.id)

        # Get recent health logs
        health_logs = crud.get_health_logs_by_pet_id(pet.id)
        latest_weight = health_logs[0] if health_logs else None

        # Count tasks by status
        pending_count = sum(1 for t in tasks if t.status == models.PetCareTaskStatus.ASSIGNED)
        awaiting_approval = sum(1 for t in tasks if t.status == models.PetCareTaskStatus.PENDING_APPROVAL)

        overview.append(
            {
                "pet": pet_with_age.model_dump(),
                "care_recommendations": care_rec.model_dump(),
                "latest_weight": latest_weight.model_dump() if latest_weight else None,
                "pending_tasks": pending_count,
                "awaiting_approval": awaiting_approval,
            }
        )

    return {"pets": overview}
