from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.user.schemas import UserCreate, UserResponse


class UserRepositoryPort(ABC):
    @abstractmethod
    async def create(
        self, data: UserCreate
    ) -> UserResponse: ...

    @abstractmethod
    async def get_by_id(
        self, user_id: UUID
    ) -> UserResponse | None: ...

    @abstractmethod
    async def store_api_key(
        self, user_id: UUID, api_key: str
    ) -> None: ...

    @abstractmethod
    async def get_api_key(
        self, user_id: UUID
    ) -> str | None: ...

