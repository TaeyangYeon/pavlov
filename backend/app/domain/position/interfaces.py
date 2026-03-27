"""
PositionRepositoryPort interface for position data operations.
Follows ABC pattern for SOLID Dependency Inversion principle.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from .schemas import PositionCreate, PositionResponse


class PositionRepositoryPort(ABC):
    """Abstract interface for position repository operations."""

    @abstractmethod
    async def create(self, data: PositionCreate, user_id: UUID) -> PositionResponse:
        """
        Create a new position.

        Args:
            data: Position creation data
            user_id: ID of the user creating the position

        Returns:
            Created position response
        """
        pass

    @abstractmethod
    async def get_by_id(self, position_id: UUID) -> PositionResponse | None:
        """
        Get position by ID.

        Args:
            position_id: Position unique identifier

        Returns:
            Position response or None if not found
        """
        pass

    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> list[PositionResponse]:
        """
        Get all positions for a user.

        Args:
            user_id: User unique identifier

        Returns:
            List of user's positions
        """
        pass

    @abstractmethod
    async def get_open_positions(self, user_id: UUID) -> list[PositionResponse]:
        """
        Get only open positions for a user.

        Args:
            user_id: User unique identifier

        Returns:
            List of user's open positions
        """
        pass

    @abstractmethod
    async def update(self, position_id: UUID, data: dict) -> PositionResponse | None:
        """
        Update position data.

        Args:
            position_id: Position unique identifier
            data: Update data dictionary

        Returns:
            Updated position or None if not found
        """
        pass

    @abstractmethod
    async def delete(self, position_id: UUID) -> bool:
        """
        Delete a position.

        Args:
            position_id: Position unique identifier

        Returns:
            True if deleted successfully
        """
        pass
