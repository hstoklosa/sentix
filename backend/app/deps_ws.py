from typing import Tuple, Optional
from urllib.parse import parse_qs

from fastapi import WebSocket, status
from sqlmodel import Session
from jose import JWTError

from app.core.db import get_session
from app.core.security import decode_token, verify_token_type, get_token_jti
from app.core.exceptions import InvalidTokenException
from app.services.token import is_token_blacklisted
from app.services.user import get_user_by_id
from app.models.user import User


async def get_token_from_query(websocket: WebSocket) -> Optional[str]:
    """
    Extract the token from the WebSocket query parameters.
    
    Args:
        websocket: The WebSocket connection
        
    Returns:
        The token if found, None otherwise
    """
    # Get query parameters from the URL
    query_string = websocket.scope.get("query_string", b"").decode()
    query_params = parse_qs(query_string)
    
    # Extract token from query parameters
    token = query_params.get("token", [None])[0]
    return token


async def verify_ws_token(websocket: WebSocket) -> Tuple[bool, Optional[dict]]:
    """
    Verify the token from the WebSocket connection.
    
    Args:
        websocket: The WebSocket connection
        
    Returns:
        A tuple of (is_valid, token_payload)
    """
    token = await get_token_from_query(websocket)
    if not token:
        return False, None
    
    try:
        # Get a database session - don't use async with since get_session is not an async context manager
        session = next(get_session())
        
        payload = decode_token(token)
        verify_token_type(payload, "access")
        
        # Check if token is blacklisted
        jti = get_token_jti(payload)
        if jti and is_token_blacklisted(session=session, jti=jti):
            return False, None
            
        return True, payload
    except JWTError:
        return False, None


async def get_current_ws_user(websocket: WebSocket) -> Optional[User]:
    """
    Get the current user from the WebSocket connection.
    
    Args:
        websocket: The WebSocket connection
        
    Returns:
        The user if authenticated, None otherwise
    """
    is_valid, payload = await verify_ws_token(websocket)
    
    if not is_valid or not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    
    # Get a database session - don't use async with
    session = next(get_session())
    user = get_user_by_id(session=session, user_id=user_id)
    return user


async def authenticate_ws_connection(websocket: WebSocket) -> Tuple[bool, Optional[User]]:
    """
    Authenticate a WebSocket connection.
    
    Args:
        websocket: The WebSocket connection
        
    Returns:
        A tuple of (is_authenticated, user)
    """
    user = await get_current_ws_user(websocket)
    
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False, None
    
    return True, user 