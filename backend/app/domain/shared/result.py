"""
Result monad for operations that can fail gracefully.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class Result(Generic[T]):
    """
    Result monad for operations that can fail gracefully.
    Use for: market data fetch, cache lookup, optional ops.
    Do NOT use for: auth failures, config errors (raise those).
    """
    value: T | None
    error: str | None
    success: bool

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        return cls(value=value, error=None, success=True)

    @classmethod
    def fail(cls, error: str) -> Result[T]:
        return cls(value=None, error=error, success=False)

    def unwrap(self) -> T:
        """Get value or raise if failure."""
        if not self.success or self.value is None:
            raise ValueError(
                f"Result.unwrap() called on failure: "
                f"{self.error}"
            )
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get value or return default if failure."""
        return self.value if self.success else default

    def map(
        self, func: Callable[[T], U]
    ) -> Result[U]:
        """Transform value if success."""
        if not self.success:
            return Result.fail(self.error or "Unknown")
        try:
            return Result.ok(func(self.value))
        except Exception as e:
            return Result.fail(str(e))

    def is_ok(self) -> bool:
        return self.success

    def is_err(self) -> bool:
        return not self.success
