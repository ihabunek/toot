from click import ClickException


class ApiError(ClickException):
    """Raised when an API request fails for whatever reason."""


class NotFoundError(ApiError):
    """Raised when an API requests returns a 404."""


class AuthenticationError(ApiError):
    """Raised when login fails."""


class ConsoleError(ClickException):
    """Raised when an error occurs which needs to be show to the user."""
