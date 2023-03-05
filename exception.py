"""Module contains custom exceptions."""


class NoEnvValueException(Exception):
    """Exception is used for issues with env constants."""

    pass


class WrongTokenException(Exception):
    """Exception is used for issues with tokens."""

    pass


class GeneralProgramException(Exception):
    """Exception is used for issues with a whole program."""

    pass


class WrongAPIAnswerStructureException(Exception):
    """Exception is used for issues with an API answer structure."""

    pass


class UnexpectedAPIAnswerException(Exception):
    """Exception is used for issues with unexpected API answers."""

    pass


class UnexpectedAPIAnswerStatusException(Exception):
    """Exception is used for issues with an unexpected API answer status."""

    pass


class WrongHomeworkStatusException(Exception):
    """Exception is used for issues with a homework status."""

    pass


class DoesntSendMessagesException(Exception):
    """Exception is used for issues with sending a message."""

    pass


class WrongHomeworkStructureException(Exception):
    """Exception is used for issues with a homework structure."""

    pass


class RequestFailedException(Exception):
    """Exception is used for issues with an API request."""

    pass
