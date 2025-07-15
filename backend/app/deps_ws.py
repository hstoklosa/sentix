from typing import Tuple, Optional
from urllib.parse import parse_qs

from fastapi import WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import sessionmanager
from app.core.security import decode_token, verify_token_type
from app.services.user import get_user_by_id
from app.models.user import User
import jwt


async def get_token_from_query(websocket: WebSocket) -> Optional[str]:
    # Get query parameters from the URL
    query_string = websocket.scope.get("query_string", b"").decode()
    query_params = parse_qs(query_string, keep_blank_values=True)
    
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

    async with sessionmanager.session() as session:
        user = await get_user_by_id(session=session, user_id=user_id)
        return user


async def authenticate_ws_connection(websocket: WebSocket) -> Tuple[bool, Optional[User]]:
    user = await get_current_ws_user(websocket)
    
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False, None
    
    return True, user 