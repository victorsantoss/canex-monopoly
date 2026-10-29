class GameError(Exception):
    """Base class for every rule violation raised by the domain."""


class InvalidSeatCountError(GameError):
    pass


class InvalidPlayerNameError(GameError):
    pass


class GameFullError(GameError):
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
