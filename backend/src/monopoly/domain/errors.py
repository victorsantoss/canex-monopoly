class GameError(Exception):
    pass


class InvalidSeatCountError(GameError):
    pass


class InvalidPlayerNameError(GameError):
    pass


class GameAlreadyStartedError(GameError):
    pass


class GameNotInProgressError(GameError):
    pass


class NotYourTurnError(GameError):
    pass


class UnknownPlayerError(GameError):
    pass


class InvalidRollError(GameError):
    pass


class InvalidGameSettingsError(GameError):
    pass
