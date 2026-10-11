from core.exceptions import BusinessException, ErrorType


class TacheNotFoundException(BusinessException):
    def __init__(self):
        super().__init__("Cette tâche n’existe pas.", ErrorType.NOT_FOUND)


class TacheInvalideException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.VALIDATION_ERROR)
