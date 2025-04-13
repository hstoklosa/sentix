from typing import Tuple, Optional
from urllib.parse import parse_qs

from fastapi import WebSocket, status
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session
import jwt

from app.core.db import get_session
from app.core.security import decode_token, verify_token_type
from app.core.exceptions import InvalidTokenException
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
        payload = decode_token(token)
        verify_token_type(payload, "access")
        return True, payload
    except jwt.exceptions.PyJWTError:
        return False, None


async def get_current_ws_user(websocket: WebSocket) -> Optional[User]:
    """
    Get the current user from the WebSocket connection using async-compatible DB access.
    
    Args:
        websocket: The WebSocket connection
        
    Returns:
        The user if authenticated, None otherwise
    """
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

    # Define a synchronous function for database access
    def _get_user_sync(user_id_int: int) -> Optional[User]:
        # This inner function runs in the threadpool
        # It gets its own session and performs the synchronous DB operation
        db_session: Session = next(get_session())
        try:
            user = get_user_by_id(session=db_session, user_id=user_id_int)
            # Eagerly load relationships if needed, or handle detached instances later
            # Example: if user: db_session.refresh(user, attribute_names=['items']) 
            return user
        finally:
            # Depending on how get_session is implemented, explicit closing might be needed
            # or handled by FastAPI's middleware. Assuming middleware handles it.
            # db_session.close() 
            pass

    # Run the synchronous database call in a threadpool
    user = await run_in_threadpool(_get_user_sync, user_id)
    
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