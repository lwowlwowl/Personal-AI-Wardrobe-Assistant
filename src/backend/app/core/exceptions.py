"""Application-level business errors; routes map them to HTTP responses."""


class AppError(Exception):
    """Expected business failure with a suggested HTTP status code."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
