import json

from cryptography.fernet import Fernet, InvalidToken

from app.domain.user.exceptions import EncryptionConfigError

CURRENT_KEY_VERSION = 1


class EncryptionService:
    """
    Symmetric encryption using Fernet (AES-128-CBC + HMAC).
    Stores ciphertext with key version for rotation support.
    Pure utility class: no I/O, no async, no side effects.
    """

    def __init__(self, key: str):
        if not key:
            raise EncryptionConfigError(
                "ENCRYPTION_KEY is required but not set"
            )
        try:
            self._fernet = Fernet(key.encode()
                                  if isinstance(key, str)
                                  else key)
        except Exception as e:
            raise EncryptionConfigError(
                f"Invalid ENCRYPTION_KEY: {e}"
            ) from e

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        Returns JSON: {"v": 1, "ciphertext": "base64..."}
        Same plaintext → different ciphertext (random IV).
        """
        if not plaintext:
            raise EncryptionError(
                "Cannot encrypt empty or None value"
            )
        encrypted_bytes = self._fernet.encrypt(
            plaintext.encode("utf-8")
        )
        payload = {
            "v": CURRENT_KEY_VERSION,
            "ciphertext": encrypted_bytes.decode("utf-8")
        }
        return json.dumps(payload)

    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt stored value.
        Expects JSON: {"v": 1, "ciphertext": "..."}
        Raises EncryptionError on any failure.
        """
        try:
            payload = json.loads(encrypted_value)
            ciphertext = payload["ciphertext"]
            decrypted_bytes = self._fernet.decrypt(
                ciphertext.encode("utf-8")
            )
            return decrypted_bytes.decode("utf-8")
        except InvalidToken as e:
            raise EncryptionError(
                "Decryption failed: invalid token "
                "(wrong key or tampered data)"
            ) from e
        except (json.JSONDecodeError, KeyError) as e:
            raise EncryptionError(
                f"Decryption failed: invalid format: {e}"
            ) from e
        except Exception as e:
            raise EncryptionError(
                f"Decryption failed: {e}"
            ) from e


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass

