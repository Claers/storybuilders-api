import base64
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel

from . import models, schemas
from .database import get_db
from sqlalchemy.orm import Session
from .config import settings


class Settings(BaseModel):
    authjwt_algorithm: str = settings.JWT_ALGORITHM
    authjwt_decode_algorithms: List[str] = [settings.JWT_ALGORITHM]
    authjwt_token_location: set = {"cookies", "headers"}
    authjwt_access_cookie_key: str = "access_token"
    authjwt_refresh_cookie_key: str = "refresh_token"
    authjwt_cookie_csrf_protect: bool = True
    # authjwt_public_key: str = base64.b64decode(settings.JWT_PUBLIC_KEY).decode("utf-8")
    # authjwt_private_key: str = base64.b64decode(settings.JWT_PRIVATE_KEY).decode(
    #     "utf-8"
    # )
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: set = {"access", "refresh"}
    authjwt_secret_key = base64.b64decode(settings.JWT_SECRET_KEY).decode("utf-8")


# A storage engine to save revoked tokens. in production,
# you can use Redis for storage system
denylist = set()

# For this example, we are just checking if the tokens jti
# (unique identifier) is in the denylist set. This could
# be made more complex, for example storing the token in Redis
# with the value true if revoked and false if not revoked
@AuthJWT.token_in_denylist_loader
def check_if_token_in_denylist(decrypted_token):
    jti = decrypted_token["jti"]
    return jti in denylist


@AuthJWT.load_config
def get_config():
    return Settings()


class NotVerified(Exception):
    pass


class UserNotFound(Exception):
    pass


reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name="JWT",
    scopes={
        "me": "Read information about the current user.",
        "admin": "Create and Delete Items.",
    },
)


def require_user(
    security_scopes: SecurityScopes,
    db: Session = Depends(get_db),
    token: str = Depends(reuseable_oauth),
    Authorize: AuthJWT = Depends(),
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"

    try:
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()
        scopes = Authorize.get_raw_jwt().get("scopes", [])

        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user:
            raise UserNotFound("User no longer exist")

        if not user.verified:
            raise NotVerified("You are not verified")
    except Exception as e:
        error = e.__class__.__name__
        print(error)
        if error == "MissingTokenError":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not logged in"
            )
        if error == "UserNotFound":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exist"
            )
        if error == "NotVerified":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your account",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired",
        )
    for scope in security_scopes.scopes:
        if scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user.id
