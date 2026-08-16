"""
Shared FastAPI dependencies: DB session + current-authenticated-user.

`get_current_user` is the single choke point every protected route depends
on (directly or via `get_current_user_id`). A missing/invalid/expired token
always yields 401 with a `WWW-Authenticate: Bearer` header, never a 500 or
a silently-anonymous request.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, bearer_scheme
from app.db.session import get_db
from app.models.user import User


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    user_id = decode_access_token(token)

    if user_id is None:
        raise credentials_exception

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user