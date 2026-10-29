class UpstreamError(Exception):
    """An upstream provider failed. The message is safe to show to users."""

    def __init__(self, message: str = "The weather service is unavailable right now.") -> None:
        super().__init__(message)
        self.message = message
