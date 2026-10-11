from core.exceptions import BusinessException, ErrorType


class ProNotFoundException(BusinessException):
    def __init__(self):
        super().__init__("Cette fiche n’existe pas.", ErrorType.NOT_FOUND)


class ProInvalideException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.VALIDATION_ERROR)
