from core.exceptions import BusinessException, ErrorType


class DecisionNotFoundException(BusinessException):
    def __init__(self):
        super().__init__("Ce sujet n’existe pas.", ErrorType.NOT_FOUND)


class DecisionInvalideException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.VALIDATION_ERROR)


class DecisionInterditeException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.FORBIDDEN)
