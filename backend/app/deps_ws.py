from typing import Tuple, Optional
from urllib.parse import parse_qs

from fastapi import WebSocket, status
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session
import jwt

from app.core.db import get_session
from app.core.security import decode_token, verify_token_type
from app.services.user import get_user_by_id
from app.models.user import User


async def get_token_from_query(websocket: WebSocket) -> Optional[str]:
    # Get query parameters from the URL
    query_string = websocket.scope.get("query_string", b"").decode()
    query_params = parse_qs(query_string)
    
    # Extract token from query parameters
    token = query_params.get("token", [None])[0]
    return token


async def verify_ws_token(websocket: WebSocket) -> Tuple[bool, Optional[dict]]:
    token = await get_token_from_query(websocket)
    if not token:
        return False, None
    
    try:
        payload = decode_token(token)
        if payload is None:
            return False, None
        if not verify_token_type(payload, "access"):
            return False, None
            
        return True, payload
    except jwt.exceptions.PyJWTError:
        return False, None


async def get_current_ws_user(websocket: WebSocket) -> Optional[User]:
    is_valid, payload = await verify_ws_token(websocket)
    
    if not is_valid or not payload:
        return None
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        return None
    
    try:
        user_id = int(user_id_str)
    except (TypeError, ValueError):
        return None

    def _get_user_sync(user_id_int: int) -> Optional[User]:
        db_session: Session = next(get_session())
        try:
            user = get_user_by_id(session=db_session, user_id=user_id_int)
            return user
        finally:
            pass

    # Run the synchronous database call in a threadpool
    user = await run_in_threadpool(_get_user_sync, user_id)
    return user


async def authenticate_ws_connection(websocket: WebSocket) -> Tuple[bool, Optional[User]]:
    user = await get_current_ws_user(websocket)
    
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False, None
    
    return True, user 