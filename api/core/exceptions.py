from enum import Enum


class ErrorType(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"


class BusinessException(Exception):
    """Erreur métier : le message est en français et peut être montré tel quel à l'équipe."""

    def __init__(self, message: str, error_type: ErrorType):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
