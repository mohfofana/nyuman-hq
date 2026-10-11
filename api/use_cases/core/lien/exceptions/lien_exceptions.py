from core.exceptions import BusinessException, ErrorType


class LienInvalideException(BusinessException):
    def __init__(self):
        super().__init__(
            "Ce lien n’est plus valable : il a déjà servi ou il a expiré. Demande un nouveau lien.",
            ErrorType.UNAUTHORIZED,
        )
