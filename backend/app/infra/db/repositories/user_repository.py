from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.interfaces import UserRepositoryPort
from app.domain.user.schemas import UserCreate, UserResponse
from app.infra.crypto.encryption import EncryptionError, EncryptionService
from app.infra.db.models.user import User


class UserRepository(UserRepositoryPort):
    def __init__(
        self,
        session: AsyncSession,
        encryption: EncryptionService,
    ):
        self._session = session
        self._encryption = encryption

    async def create(
        self, data: UserCreate
    ) -> UserResponse:
        user = User(email=data.email)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return self._to_response(user)

    async def get_by_id(
        self, user_id: UUID
    ) -> UserResponse | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_response(row) if row else None

    async def store_api_key(
        self, user_id: UUID, api_key: str
    ) -> None:
        """Encrypt API key before storing."""
        encrypted = self._encryption.encrypt(api_key)
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(api_key_encrypted=encrypted)
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_api_key(
        self, user_id: UUID
    ) -> str | None:
        """Fetch and decrypt API key."""
        stmt = select(User.api_key_encrypted).where(
            User.id == user_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None or not row:
            return None
        try:
            return self._encryption.decrypt(row)
        except EncryptionError:
            print(
                f"[UserRepository] Failed to decrypt "
                f"api_key for user {user_id}"
            )
            return None

    def _to_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            has_api_key=bool(user.api_key_encrypted),
            is_active=user.is_active,
            created_at=user.created_at,
        )
