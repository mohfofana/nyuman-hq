from core.exceptions import BusinessException, ErrorType


class RetourNotFoundException(BusinessException):
    def __init__(self):
        super().__init__("Ce retour n’existe pas.", ErrorType.NOT_FOUND)


class RetourInvalideException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.VALIDATION_ERROR)


class TestflightNonBrancheException(BusinessException):
    def __init__(self):
        super().__init__(
            "L’import TestFlight n’est pas branché : il faut une clé App Store Connect sur le serveur.",
            ErrorType.VALIDATION_ERROR,
        )
