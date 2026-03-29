"""
Position domain exceptions.
"""


class PositionNotFoundError(Exception):
    """Raised when a position is not found."""
    pass


class InvalidPriceError(Exception):
    """Raised when an invalid price is provided."""
    pass
