import uuid
from datetime import timedelta, datetime, timezone
from typing import Annotated, Generator, Any
from fastapi import APIRouter, Depends, HTTPException
from src.schemas import User, Token
from sqlalchemy.orm import Session

from starlette import status
from src.service import SessionLocal
from src.models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")

print(SECRET_KEY, ALGORITHM)
router = APIRouter(prefix="/auth", tags=["auth"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: User) -> None:
    create_user_model = Users(
        id=uuid.uuid4(),
        name=create_user_request.name,
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
    )
    db.add(create_user_model)
    db.commit()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
) -> dict[str, str]:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
    token = create_access_token(user.name, user.id, timedelta(minutes=30))

    return {"access_token": token, "token_type": "bearer"}


def authenticate_user(username: str, password: str, db: Session) -> Users | None:
    user: Users | None = db.query(Users).filter(Users.email == username).first()
    if not user:
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(name: str, user_id: uuid.UUID, expires_delta: timedelta) -> str | Any:
    if SECRET_KEY is None or ALGORITHM is None:
        raise ValueError("SECRET_KEY or ALGORITHM environment variable is not set")
    payload = {"sub": name, "id": str(user_id), "exp": datetime.now(timezone.utc) + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> dict[str, str | uuid.UUID]:
    if SECRET_KEY is None or ALGORITHM is None:
        raise ValueError("SECRET_KEY or ALGORITHM environment variable is not set")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email = payload.get("sub")
        if not isinstance(email, str):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload: email missing")
        user_id = payload.get("id")
        if not isinstance(user_id, str):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload: id missing")
        if email is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        return {"email": email, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
