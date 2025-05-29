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

from fastapi import Depends, FastAPI, HTTPException, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # noqa: E402
from mangum import Mangum  # Import Mangum # noqa: E402

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
handler = Mangum(app, lifespan="off")


@app.options("/token")
async def options_token():
    return {"message": "OK"}

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
    current_kid: models.User = Depends(get_current_kid_user),  # noqa: B008
):
    """
    Kid submits a chore they have completed. Creates a ChoreLog entry with PENDING_APPROVAL status.
    """
    chore_log = crud.create_chore_log_submission(chore_id=chore_id, kid_user=current_kid)
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


# --- Character Endpoints ---
@app.post("/characters/", response_model=models.Character, status_code=status.HTTP_201_CREATED)
async def create_character(
    character: models.CharacterCreate,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Create a new character (parent only)."""
    return crud.create_character(character_in=character)


@app.get("/characters/", response_model=List[models.Character])  # noqa: UP006
async def get_all_characters(
    current_user: models.User = Depends(get_current_user),  # noqa: B008
):
    """Get all characters."""
    return crud.get_all_characters()


@app.get("/characters/available/", response_model=List[models.Character])  # noqa: UP006
async def get_available_characters(
    current_user: models.User = Depends(get_current_user),  # noqa: B008
):
    """Get characters available to the current user based on their points."""
    return crud.get_available_characters_for_user(user_id=current_user.id)


@app.get("/characters/{character_id}", response_model=models.Character)
async def get_character(
    character_id: str,
    current_user: models.User = Depends(get_current_user),  # noqa: B008
):
    """Get a specific character by ID."""
    character = crud.get_character_by_id(character_id=character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@app.put("/characters/{character_id}", response_model=models.Character)
async def update_character(
    character_id: str,
    character: models.CharacterCreate,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Update a character (parent only)."""
    updated_character = crud.update_character(character_id=character_id, character_in=character)
    if not updated_character:
        raise HTTPException(status_code=404, detail="Character not found")
    return updated_character


@app.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: str,
    current_parent: models.User = Depends(get_current_parent_user),  # noqa: B008
):
    """Delete a character (parent only)."""
    success = crud.delete_character(character_id=character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return None


@app.get("/users/me/character", response_model=Optional[models.Character])
async def get_my_character(
    current_user: models.User = Depends(get_current_user),  # noqa: B008
):
    """Get the current user's selected character."""
    return crud.get_user_character(user_id=current_user.id)


class SetCharacterRequest(BaseModel):
    character_id: str
    customization: Optional[models.AvatarCustomization] = None


@app.post("/users/me/character", status_code=status.HTTP_200_OK)
async def set_my_character(
    request: SetCharacterRequest,
    current_user: models.User = Depends(get_current_user),  # noqa: B008
):
    """Set the current user's character with optional customization."""
    success = crud.set_user_character(
        user_id=current_user.id, 
        character_id=request.character_id,
        customization=request.customization
    )
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Failed to set character. Character may not exist or you don't have enough points to unlock it."
        )
    return {"message": "Character set successfully"}
