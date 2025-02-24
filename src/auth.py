import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from starlette import status
from starlette.responses import Response, JSONResponse

from src.schemas import CurrentUser

load_dotenv()

OAUTH_SECRET_KEY = os.environ.get("OAUTH_SECRET_KEY", "")
_OAUTH_ALGORITHM = "HS256"


oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/token")


def create_access_token(name: str, user_id: uuid.UUID, expires_delta: timedelta) -> str:
    payload = {"sub": name, "id": str(user_id), "exp": datetime.now(timezone.utc) + expires_delta}
    return jwt.encode(payload, OAUTH_SECRET_KEY, algorithm=_OAUTH_ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> CurrentUser:
    try:
        payload = jwt.decode(token, OAUTH_SECRET_KEY, algorithms=_OAUTH_ALGORITHM)
        email = payload["sub"]
        user_id = payload["id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token payload: {e.args[0]} missing"
        )
    return CurrentUser(id=user_id, email=email)


async def auth_middleware(request: Request, call_next) -> Response:
    public_routes = {"/", "/token", "/auth", "/docs", "/openapi.json"}

    if request.url.path in public_routes:
        return await call_next(request)

    authorization = request.headers.get("Authorization")
    if not authorization:
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing authorization token"})
    token = authorization.split(" ")[-1]
    user = await get_current_user(token)
    request.state.user = user
    return await call_next(request)
