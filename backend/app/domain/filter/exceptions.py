"""
Filter-related exceptions.
"""


class FilterConfigError(Exception):
    """Raised when filter is configured with invalid params."""

    def __init__(self, filter_name: str, reason: str):
        super().__init__(f"Invalid config for {filter_name}: {reason}")
        self.filter_name = filter_name
        self.reason = reason
