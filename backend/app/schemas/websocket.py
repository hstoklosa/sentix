from pydantic import BaseModel, Field


class WebSocketConnectionInfo(BaseModel):
    """
    Schema for WebSocket connection information.
    
    Attributes:
        websocket_url: The URL to connect to the WebSocket, including the authentication token
    """
    websocket_url: str = Field(
        ..., 
        description="The URL to connect to the WebSocket, including the authentication token"
    ) 