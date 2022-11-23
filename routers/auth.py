from datetime import timedelta
from fastapi import (
    APIRouter,
    Request,
    Response,
    status,
    Depends,
    HTTPException,
    Security,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from app import oauth2
from .. import schemas, models, utils
from sqlalchemy.orm import Session
from ..database import get_db
from app.oauth2 import AuthJWT, denylist
from ..config import settings


router = APIRouter()
ACCESS_TOKEN_EXPIRES_IN = settings.ACCESS_TOKEN_EXPIRES_IN
REFRESH_TOKEN_EXPIRES_IN = settings.REFRESH_TOKEN_EXPIRES_IN

# Register a new user
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserResponse,
)
async def create_user(
    payload: schemas.CreateUserSchema,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends(),
    user_id: str = Security(oauth2.require_user, scopes=["admin"]),
):
    Authorize.jwt_required()

    current_user = Authorize.get_jwt_subject()
    # Check if user already exist
    user = (
        db.query(models.User)
        .filter(models.User.email == EmailStr(payload.email.lower()))
        .first()
    )
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exist"
        )
    # Compare password and passwordConfirm
    if payload.password != payload.passwordConfirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )
    #  Hash the password
    payload.password = utils.hash_password(payload.password)
    del payload.passwordConfirm
    payload.role = "user"
    payload.verified = True
    payload.email = EmailStr(payload.email.lower())
    payload.created_by = current_user
    new_user = models.User(**payload.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# Login user
@router.post("/login", response_model=schemas.TokenSchema)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = "",
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends(),
):
    # Check if the user exist
    user = (
        db.query(models.User)
        .filter(models.User.email == EmailStr(form_data.username.lower()))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect Email or Password",
        )

    # Check if user verified his email
    if not user.verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email address",
        )
    # Check if the password is valid
    if not utils.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect Email or Password",
        )

    # Create access token
    access_token = Authorize.create_access_token(
        subject=str(user.id),
        expires_time=timedelta(minutes=ACCESS_TOKEN_EXPIRES_IN),
        user_claims={"scopes": user.scopes.split(",")},
    )

    # Create refresh token
    refresh_token = Authorize.create_refresh_token(
        subject=str(user.id),
        expires_time=timedelta(minutes=REFRESH_TOKEN_EXPIRES_IN),
        user_claims={"scopes": user.scopes.split(",")},
    )

    # Store refresh and access tokens in cookie
    response.set_cookie(
        "access_token",
        access_token,
        ACCESS_TOKEN_EXPIRES_IN * 60,
        ACCESS_TOKEN_EXPIRES_IN * 60,
        "/",
        None,
        False,
        True,
        "lax",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        REFRESH_TOKEN_EXPIRES_IN * 60,
        REFRESH_TOKEN_EXPIRES_IN * 60,
        "/",
        None,
        False,
        True,
        "lax",
    )
    response.set_cookie(
        "logged_in",
        "True",
        ACCESS_TOKEN_EXPIRES_IN * 60,
        ACCESS_TOKEN_EXPIRES_IN * 60,
        "/",
        None,
        False,
        False,
        "lax",
    )

    # Send both access
    return {"status": "success", "access_token": access_token}


# Refresh access token
@router.get("/refresh")
def refresh_token(
    response: Response,
    request: Request,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
    user_id: str = Depends(oauth2.require_user),
):
    try:
        Authorize.jwt_refresh_token_required()

        user_id = Authorize.get_jwt_subject()
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh access token",
            )
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The user belonging to this token no logger exist",
            )
        access_token = Authorize.create_access_token(
            subject=str(user.id),
            expires_time=timedelta(minutes=ACCESS_TOKEN_EXPIRES_IN),
        )
    except Exception as e:
        error = e.__class__.__name__
        if error == "MissingTokenError":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide refresh token",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    response.set_cookie(
        "access_token",
        access_token,
        ACCESS_TOKEN_EXPIRES_IN * 60,
        ACCESS_TOKEN_EXPIRES_IN * 60,
        "/",
        None,
        False,
        True,
        "lax",
    )
    response.set_cookie(
        "logged_in",
        "True",
        ACCESS_TOKEN_EXPIRES_IN * 60,
        ACCESS_TOKEN_EXPIRES_IN * 60,
        "/",
        None,
        False,
        False,
        "lax",
    )
    return {"access_token": access_token}


# Logout user
@router.get("/logout", status_code=status.HTTP_200_OK)
def logout(
    response: Response,
    Authorize: AuthJWT = Depends(),
    user_id: str = Depends(oauth2.require_user),
):
    Authorize.unset_jwt_cookies()
    denylist.add(Authorize.get_raw_jwt()["jti"])
    response.set_cookie("logged_in", "", -1)

    return {"status": "success"}
