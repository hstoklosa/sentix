from fastapi import HTTPException, status


class APIException(HTTPException):
    """Base API exception class that extends FastAPI's HTTPException."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error"
    headers = {}

    def __init__(self, detail=None, headers=None):
        self.detail = detail or self.detail
        self.headers = headers or self.headers
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=self.headers
        )


class AuthenticationException(APIException):
    """Base exception for authentication-related errors."""
    status_code = status.HTTP_401_UNAUTHORIZED
    headers = {"WWW-Authenticate": "Bearer"}


class BadRequestException(APIException):
    """Base exception for bad request errors."""
    status_code = status.HTTP_400_BAD_REQUEST


class ForbiddenException(APIException):
    """Base exception for forbidden action errors."""
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundException(APIException):
    """Base exception for not found errors."""
    status_code = status.HTTP_404_NOT_FOUND


# Authentication specific exceptions
class InvalidCredentialsException(AuthenticationException):
    detail = "Invalid email or password"


class InvalidTokenException(AuthenticationException):
    detail = "Invalid token"
    
    def __init__(self, detail=None, headers=None):
        super().__init__(
            detail=detail or self.detail,
            headers=headers
        )


# Input validation exceptions
class InvalidPasswordException(BadRequestException):
    detail = "Password does not meet security requirements"


class ResourceExistsException(BadRequestException):
    """Exception for when a resource already exists."""
    detail = "Resource already exists"


class DuplicateEmailException(ResourceExistsException):
    detail = "The provided email address is already registered"


class DuplicateUsernameException(ResourceExistsException):
    detail = "The provided username is already taken"