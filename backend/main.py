# Assuming main.py, crud.py, models.py, security.py are all in LAMBDA_TASK_ROOT (/var/task)
# and __init__.py makes this directory a package.
# For Lambda containers, often direct imports work if LAMBDA_TASK_ROOT is in sys.path.
from datetime import timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from mangum import Mangum

import crud
import models
import security

# --- Authentication Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- Dependency to get current user ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_payload = security.decode_access_token(token)
    if not token_payload or "username" not in token_payload or "family_id" not in token_payload:
        raise credentials_exception

    user = crud.get_user_by_username(username=token_payload["username"], family_id=token_payload["family_id"])
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


# --- Dependency for Parent-only actions ---
async def get_current_parent_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:
    if current_user.role != models.UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role",
        )
    if not current_user.family_id:
        raise HTTPException(status_code=403, detail="Parent user is not associated with a family.")
    return current_user


# --- Dependency for Kid-only actions ---
async def get_current_kid_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:
    if current_user.role != models.UserRole.KID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role",
        )
    if not current_user.family_id:
        raise HTTPException(status_code=403, detail="Kid user is not associated with a family.")
    if current_user.points is None:
        current_user.points = 0
    return current_user


app = FastAPI()

# --- CORS Middleware ---
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3000",
    "https://main.dd0mqanef4wnt.amplifyapp.com",
    "https://monkeypoints.shop",
    "https://www.monkeypoints.shop",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoints ---

# Lambda handler - Mangum wraps the FastAPI app
handler = Mangum(app)


@app.post("/token", response_model=models.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.authenticate_user(form_data.username, form_data.password)
    if not user or not user.family_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password, or user not in a family.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username, "family_id": user.family_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "family_id": user.family_id}


@app.post("/users/", response_model=models.User, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: models.UserCreate):
    existing_user = None
    if user_in.family_id:
        existing_user = crud.get_user_by_username(username=user_in.username, family_id=user_in.family_id)
    elif not user_in.family_name:
        pass

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered in this family.")

    created_user = crud.create_user(user_in=user_in)
    if not created_user:
        raise HTTPException(status_code=500, detail="Could not create user.")
    return created_user


@app.get("/users/me/", response_model=models.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/", response_model=List[models.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_parent: models.User = Depends(get_current_parent_user)
):
    users = crud.get_all_users(family_id=current_parent.family_id)
    return users[skip : skip + limit]


@app.post("/users/promote", response_model=models.User)
async def promote_user_to_parent_role(
    request: models.UserPromoteRequest,
    current_admin_user: models.User = Depends(get_current_parent_user),
):
    user_to_promote = crud.get_user_by_username(request.username, family_id=current_admin_user.family_id)
    if not user_to_promote:
        raise HTTPException(status_code=404, detail=f"User {request.username} not found in this family.")

    promoted_user = crud.promote_user_to_parent(request.username, family_id=current_admin_user.family_id)
    if not promoted_user:
        raise HTTPException(status_code=500, detail=f"Could not promote user {request.username}.")
    return promoted_user


@app.post("/store/items/", response_model=models.StoreItem, status_code=status.HTTP_201_CREATED)
async def create_item_for_store(
    item_in: models.StoreItemCreate,
    current_parent: models.User = Depends(get_current_parent_user),
):
    if item_in.family_id != current_parent.family_id:
        raise HTTPException(status_code=400, detail="Cannot create store item for a different family.")
    return crud.create_store_item(item_in=item_in, family_id=current_parent.family_id)


@app.get("/store/items/", response_model=List[models.StoreItem])
async def read_store_items(current_user: models.User = Depends(get_current_active_user)):
    items = crud.get_store_items(family_id=current_user.family_id)
    return items


@app.delete("/store/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store_item_from_store(
    item_id: str,
    current_parent: models.User = Depends(get_current_parent_user),
):
    item_to_delete = crud.get_store_item_by_id(item_id=item_id, family_id=current_parent.family_id)
    if not item_to_delete:
        raise HTTPException(status_code=404, detail="Store item not found in this family.")

    if not crud.delete_store_item(item_id=item_id, family_id=current_parent.family_id):
        raise HTTPException(status_code=500, detail="Failed to delete store item.")
    return


@app.post("/kids/points/award/", response_model=models.User)
async def award_points_to_kid(
    award: models.PointsAward,
    current_parent: models.User = Depends(get_current_parent_user),
):
    kid_user = crud.get_user_by_username(username=award.kid_username, family_id=current_parent.family_id)
    if not kid_user or kid_user.role != models.UserRole.KID:
        raise HTTPException(status_code=404, detail="Kid user not found in this family or user is not a kid.")

    updated_user = crud.update_user_points(
        username=award.kid_username, points_to_add=award.points, family_id=current_parent.family_id
    )
    if not updated_user:
        raise HTTPException(status_code=500, detail="Could not award points. Kid user may not exist or operation failed.")
    return updated_user


@app.post("/kids/store/redeem/", response_model=models.PurchaseLog)
async def kid_redeems_item(
    redemption: models.RedemptionRequest,
    current_kid: models.User = Depends(get_current_kid_user),
):
    store_item = crud.get_store_item_by_id(item_id=redemption.item_id, family_id=current_kid.family_id)
    if not store_item:
        raise HTTPException(status_code=404, detail="Item not found in your family's store.")

    if (current_kid.points or 0) < store_item.points_cost:
        raise HTTPException(status_code=400, detail="Not enough points to redeem this item.")

    updated_kid = crud.update_user_points(
        username=current_kid.username, points_to_add=-store_item.points_cost, family_id=current_kid.family_id
    )
    if not updated_kid:
        raise HTTPException(status_code=500, detail="Failed to update kid's points. Redemption aborted.")

    purchase_log = crud.create_purchase_log(
        user=updated_kid, item=store_item, family_id=current_kid.family_id
    )
    return purchase_log


@app.get("/users/me/purchases/", response_model=List[models.PurchaseLog])
async def read_my_purchase_history(current_user: models.User = Depends(get_current_active_user)):
    logs = crud.get_purchase_logs_for_user(user_id=current_user.id, family_id=current_user.family_id)
    return logs


@app.get("/family/purchases/", response_model=List[models.PurchaseLog])
async def read_family_purchase_history(current_parent: models.User = Depends(get_current_parent_user)):
    logs = crud.get_all_purchase_logs(family_id=current_parent.family_id)
    return logs


@app.post("/chores/", response_model=models.Chore, status_code=status.HTTP_201_CREATED)
async def create_new_chore(
    chore_in: models.ChoreCreate,
    current_parent: models.User = Depends(get_current_parent_user)
):
    if chore_in.family_id != current_parent.family_id:
         raise HTTPException(status_code=400, detail="Cannot create chore for a different family.")
    return crud.create_chore(chore_in=chore_in, family_id=current_parent.family_id)


@app.get("/chores/", response_model=List[models.Chore])
async def get_family_chores(
    is_active: Optional[bool] = None,
    current_user: models.User = Depends(get_current_active_user)
):
    return crud.get_chores(family_id=current_user.family_id, is_active=is_active)


@app.get("/chores/{chore_id}", response_model=models.Chore)
async def get_single_chore(
    chore_id: str,
    current_user: models.User = Depends(get_current_active_user)
):
    chore = crud.get_chore_by_id(chore_id=chore_id, family_id=current_user.family_id)
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found in this family.")
    return chore


@app.put("/chores/{chore_id}", response_model=models.Chore)
async def update_existing_chore(
    chore_id: str,
    chore_update: models.ChoreUpdate,
    current_parent: models.User = Depends(get_current_parent_user)
):
    updated_chore = crud.update_chore(chore_id=chore_id, chore_update=chore_update, family_id=current_parent.family_id)
    if not updated_chore:
        raise HTTPException(status_code=404, detail="Chore not found or update failed.")
    return updated_chore


@app.delete("/chores/{chore_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_chore(
    chore_id: str,
    current_parent: models.User = Depends(get_current_parent_user)
):
    chore_to_delete = crud.get_chore_by_id(chore_id=chore_id, family_id=current_parent.family_id)
    if not chore_to_delete:
        raise HTTPException(status_code=404, detail="Chore not found in this family.")

    success = crud.delete_chore(chore_id=chore_id, family_id=current_parent.family_id)
    if not success:
        raise HTTPException(status_code=500, detail="Chore not found or delete failed.")
    return


@app.post("/chores/log_completion/", response_model=models.ChoreLog, status_code=status.HTTP_201_CREATED)
async def log_chore_as_completed(
    log_in: models.ChoreLogCreate,
    current_user: models.User = Depends(get_current_active_user)
):
    chore_to_log = crud.get_chore_by_id(chore_id=log_in.chore_id, family_id=current_user.family_id)
    if not chore_to_log:
        raise HTTPException(status_code=404, detail="Chore not found in this family.")

    kid_user = crud.get_user_by_username(username=log_in.user_id, family_id=current_user.family_id)
    if not kid_user or kid_user.role != models.UserRole.KID:
        raise HTTPException(status_code=404, detail="Kid user not found in this family or user is not a kid.")

    return crud.log_chore_completion(
        chore_id=log_in.chore_id,
        user_id=kid_user.id,
        family_id=current_user.family_id,
        completed_by_user_id=current_user.id
    )


@app.get("/chores/logs/user/{user_id_param}", response_model=List[models.ChoreLog])
async def get_chore_logs_for_a_user(
    user_id_param: str,
    current_parent: models.User = Depends(get_current_parent_user)
):
    target_user = crud.get_user_by_id(user_id_param)
    if not target_user or target_user.family_id != current_parent.family_id or target_user.role != models.UserRole.KID:
         raise HTTPException(status_code=404, detail="Kid user not found in this family.")

    return crud.get_chore_logs_for_user(user_id=user_id_param, family_id=current_parent.family_id)


@app.get("/chores/logs/my/", response_model=List[models.ChoreLog])
async def get_my_chore_logs(
    current_kid: models.User = Depends(get_current_kid_user)
):
    return crud.get_chore_logs_for_user(user_id=current_kid.id, family_id=current_kid.family_id)


@app.get("/chores/logs/family/", response_model=List[models.ChoreLog])
async def get_all_family_chore_logs(
    current_parent: models.User = Depends(get_current_parent_user)
):
    return crud.get_all_chore_logs_for_family(family_id=current_parent.family_id)


@app.post("/requests/", response_model=models.Request, status_code=status.HTTP_201_CREATED)
async def submit_item_request(
    request_in: models.RequestCreate,
    current_kid: models.User = Depends(get_current_kid_user)
):
    store_item = crud.get_store_item_by_id(item_id=request_in.item_id, family_id=current_kid.family_id)
    if not store_item:
        raise HTTPException(status_code=404, detail="Requested item not found in family store.")

    return crud.create_request(user=current_kid, item_id=request_in.item_id, family_id=current_kid.family_id)


@app.get("/requests/family/", response_model=List[models.Request])
async def get_family_item_requests(
    status_filter: Optional[models.RequestStatus] = None,
    current_parent: models.User = Depends(get_current_parent_user)
):
    return crud.get_requests_for_family(family_id=current_parent.family_id, status=status_filter)


@app.get("/requests/my/", response_model=List[models.Request])
async def get_my_item_requests(
    status_filter: Optional[models.RequestStatus] = None,
    current_kid: models.User = Depends(get_current_kid_user)
):
    all_family_requests = crud.get_requests_for_family(family_id=current_kid.family_id, status=status_filter)
    my_requests = [req for req in all_family_requests if req.user_id == current_kid.id]
    return my_requests


@app.put("/requests/{request_id}/status", response_model=models.Request)
async def update_item_request_status(
    request_id: str,
    status_update: models.RequestStatusUpdate,
    current_parent: models.User = Depends(get_current_parent_user)
):
    updated_request = crud.update_request_status(
        request_id=request_id,
        new_status=status_update.new_status,
        family_id=current_parent.family_id,
        parent_user=current_parent
    )
    if not updated_request:
        raise HTTPException(status_code=404, detail="Request not found or update failed.")
    return updated_request


@app.post("/families/", response_model=models.Family, status_code=status.HTTP_201_CREATED)
async def create_new_family(
    family_in: models.FamilyCreate,
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.family_id:
        raise HTTPException(status_code=400, detail="User already belongs to a family.")

    updated_user = crud.assign_user_to_new_family(user_id=current_user.id, family_name=family_in.name)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to create family or assign user.")
    family_details = crud.get_family_by_id(updated_user.family_id)
    if not family_details:
        raise HTTPException(status_code=404, detail="Family created and user assigned, but could not retrieve family details.")
    return family_details


@app.get("/families/my", response_model=models.Family)
async def get_my_family_details(current_user: models.User = Depends(get_current_active_user)):
    if not current_user.family_id:
        raise HTTPException(status_code=404, detail="User is not associated with any family.")
    family = crud.get_family_by_id(current_user.family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family details not found.")
    return family


@app.get("/")
async def read_root():
    return {"message": "Kids Rewards API is running!"}


@app.get("/leaderboard", response_model=list[models.User])
async def get_leaderboard(current_user: models.User = Depends(get_current_active_user)):
    if not current_user.family_id:
        raise HTTPException(status_code=403, detail="Cannot view leaderboard without being part of a family.")
    users = crud.get_all_users(family_id=current_user.family_id)
    sorted_users = sorted(users, key=lambda u: u.points if u.points is not None else -1, reverse=True)
    return sorted_users


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
