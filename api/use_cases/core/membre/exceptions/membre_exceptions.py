from core.exceptions import BusinessException, ErrorType


class MembreNotFoundException(BusinessException):
    def __init__(self):
        super().__init__("Ce membre n’existe pas.", ErrorType.NOT_FOUND)


class AccesRefuseException(BusinessException):
    def __init__(self):
        super().__init__(
            "Cette adresse n’a pas accès à HQ. Demande à un head de t’ajouter dans les réglages.",
            ErrorType.FORBIDDEN,
        )


class ConnexionGoogleInvalideException(BusinessException):
    def __init__(self):
        super().__init__("La connexion Google n’a pas pu être vérifiée. Réessaie.", ErrorType.UNAUTHORIZED)


class ReserveAuxHeadsException(BusinessException):
    def __init__(self):
        super().__init__("Seul un head peut faire ça.", ErrorType.FORBIDDEN)


class MembreDejaPresentException(BusinessException):
    def __init__(self):
        super().__init__("Cette adresse fait déjà partie de la maison.", ErrorType.ALREADY_EXISTS)


class ModificationInterditeException(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.VALIDATION_ERROR)
