from uuid import UUID

from app.core.config import Settings
from app.domain.user.exceptions import InvalidAPIKeyError, UserNotFoundError
from app.domain.user.interfaces import UserRepositoryPort
from app.domain.user.schemas import (
    APIKeySetRequest,
    APIKeySetResponse,
    UserCreate,
    UserResponse,
)


class UserService:
    """
    User management with API key validation and storage.
    Single responsibility: user operations + key lifecycle.
    """
    def __init__(
        self,
        repository: UserRepositoryPort,
        settings: Settings,
    ):
        self._repository = repository
        self._settings = settings

    async def create_user(
        self, data: UserCreate
    ) -> UserResponse:
        return await self._repository.create(data)

    async def get_user(
        self, user_id: UUID
    ) -> UserResponse:
        user = await self._repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    async def set_api_key(
        self,
        user_id: UUID,
        request: APIKeySetRequest,
    ) -> APIKeySetResponse:
        """
        Validate API key then store encrypted.
        Raises InvalidAPIKeyError if key is invalid.
        """
        # Step 1: Validate key with Anthropic
        await self._validate_anthropic_key(
            request.api_key
        )

        # Step 2: Store encrypted
        await self._repository.store_api_key(
            user_id, request.api_key
        )

        return APIKeySetResponse(
            success=True,
            message=(
                "API key validated and stored securely"
            )
        )

    async def get_api_key(
        self, user_id: UUID
    ) -> str | None:
        """Return decrypted API key or None."""
        return await self._repository.get_api_key(user_id)

    async def _validate_anthropic_key(
        self, api_key: str
    ) -> None:
        """
        Validate API key by making minimal Anthropic call.
        Raises InvalidAPIKeyError on failure.
        """
        try:
            from app.domain.ai.anthropic_client import AnthropicClient
            client = AnthropicClient(api_key=api_key)
            # Minimal test: single token request
            test_prompt = (
                "Reply with exactly: {\"market_summary\": "
                "\"ok\", \"strategies\": []}"
            )
            await client.call(test_prompt)
        except Exception as e:
            err_str = str(e).lower()
            if "authentication" in err_str or \
               "invalid" in err_str or \
               "401" in err_str:
                raise InvalidAPIKeyError(
                    f"Key rejected by Anthropic: {e}"
                ) from e
            # Network errors → still accept key
            # (don't punish users for network issues)
            print(
                f"[UserService] API key validation "
                f"network error (key accepted): {e}"
            )

