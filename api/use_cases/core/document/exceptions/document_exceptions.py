from core.exceptions import BusinessException, ErrorType


class DocumentNotFoundException(BusinessException):
    def __init__(self):
        super().__init__("Ce document n’existe pas.", ErrorType.NOT_FOUND)


class DocumentVersionNotFoundException(BusinessException):
    def __init__(self):
        super().__init__("Cette version du document n’existe pas.", ErrorType.NOT_FOUND)


class DocumentModifieEntreTempsException(BusinessException):
    def __init__(self):
        super().__init__(
            "Quelqu’un a modifié ce document pendant que tu écrivais. Recharge pour voir sa version.",
            ErrorType.CONFLICT,
        )


class DocumentInvalideException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.VALIDATION_ERROR)


class DocumentArchiveException(BusinessException):
    def __init__(self):
        super().__init__("Ce document est dans la corbeille. Restaure-le pour le modifier.", ErrorType.VALIDATION_ERROR)
