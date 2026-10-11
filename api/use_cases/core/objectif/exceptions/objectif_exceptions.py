from core.exceptions import BusinessException, ErrorType


class ObjectifInvalideException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.VALIDATION_ERROR)
