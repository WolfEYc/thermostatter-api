import os
from datetime import datetime, timedelta
from typing import Annotated, Optional

import bcrypt
import jwt
import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from thermostatter_api.pg import PG

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


AUTH_SECRET_KEY = os.environ["AUTH_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIMEDELTA = timedelta(minutes=30)

USERS_TABLE_NAME = "auth.users"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: str
    exp: int


class User(BaseModel):
    username: str
    email: str
    active: bool
    created_at: datetime


class CreateUserReq(BaseModel):
    username: str
    email: str
    password: str


# Hash a password using bcrypt
def hash_password(password):
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password


def verify_password(plain_password: str, hashed_password: str):
    plain_password_bytes = plain_password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(
        password=plain_password_bytes, hashed_password=hashed_password_bytes
    )


def verify_token(token: str) -> TokenData:
    payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[ALGORITHM])
    token_data = TokenData.model_validate(payload)
    return token_data


def create_token(username: str) -> Token:
    exp = datetime.now() + ACCESS_TOKEN_EXPIRE_TIMEDELTA
    token_data = TokenData(sub=username, exp=int(exp.timestamp()))
    token_data = token_data.model_dump()
    token = jwt.encode(token_data, AUTH_SECRET_KEY, algorithm=ALGORITHM)
    return Token(access_token=token, token_type="bearer")


UNAUTHORIZED_EXCEPTION = HTTPException(
    status_code=401,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

INVALID_TOKEN_EXCEPTION = HTTPException(
    status_code=401,
    detail="Invalid token",
    headers={"WWW-Authenticate": "Bearer"},
)

USER_INACTIVE_EXCEPTION = HTTPException(
    status_code=403,
    detail="User is not active",
    headers={"WWW-Authenticate": "Bearer"},
)


GET_HASHED_PASSWORD_QUERY = f"SELECT hashed_password FROM {USERS_TABLE_NAME} WHERE active AND username = :username"


async def authenticate(username: str, password: str) -> Token:
    hashed_pwd_tbl = await PG.fetch(GET_HASHED_PASSWORD_QUERY, username=username)
    if hashed_pwd_tbl is None:
        raise UNAUTHORIZED_EXCEPTION
    hashed_pwd: str = hashed_pwd_tbl.item()
    if not verify_password(password, hashed_pwd):
        raise UNAUTHORIZED_EXCEPTION
    token = create_token(username)
    return token


async def get_token_data_dep(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenData:
    try:
        token_data = verify_token(token)
    except Exception:
        raise INVALID_TOKEN_EXCEPTION
    return token_data


async def get_username_dep(
    token_data: Annotated[TokenData, Depends(get_token_data_dep)],
) -> str:
    return token_data.sub


USERNAME_DEP = Annotated[str, Depends(get_username_dep)]

GET_USER_BY_USERNAME_QUERY = f"SELECT username, email, active, created_at FROM {USERS_TABLE_NAME} WHERE username = :username"


async def fetch_user_from_db(username: str) -> Optional[User]:
    user_tbl = await PG.fetch(GET_USER_BY_USERNAME_QUERY, username=username)
    if user_tbl is None:
        return None
    user_json = user_tbl.row(0, named=True)
    user = User.model_validate(user_json)
    return user


async def get_user_dep(username: USERNAME_DEP):
    user = await fetch_user_from_db(username)
    if not user:
        raise UNAUTHORIZED_EXCEPTION
    return user


USER_DEP = Annotated[User, Depends(get_user_dep)]

FAILED_TO_REGISTER_EXCEPTION = HTTPException(
    400,
    "User registration failed, likely an account with this username or email is already taken",
)


async def register(req: CreateUserReq) -> Token:
    hashed_password = hash_password(req.password)
    insert_row = {
        "hashed_password": hashed_password,
        "username": req.username,
        "email": req.email,
    }

    df = pl.DataFrame([insert_row])
    return_keys = set(User.model_fields.keys())
    user_tbl = await PG.insert(df, USERS_TABLE_NAME, return_cols=return_keys)
    if user_tbl is None:
        raise FAILED_TO_REGISTER_EXCEPTION
    user = user_tbl.row(0, named=True)
    user = User.model_validate(user)
    token = create_token(user.username)
    return token


@router.post("/token")
async def authenticate_endpoint(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    return await authenticate(form_data.username, form_data.password)


@router.get("/userinfo")
async def user_info_endpoint(current_user: USER_DEP) -> User:
    return current_user


@router.post("/register")
async def register_endpoint(req: CreateUserReq) -> Token:
    return await register(req)
