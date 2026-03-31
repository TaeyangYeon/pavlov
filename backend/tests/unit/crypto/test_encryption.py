import json
import pytest
from cryptography.fernet import Fernet

from app.domain.user.exceptions import EncryptionConfigError
from app.infra.crypto.encryption import EncryptionService, EncryptionError


class TestEncryptionService:
    """Test suite for EncryptionService (TDD Red phase)"""

    def test_encrypt_returns_string(self):
        """encrypt() should return a string, not bytes"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        
        result = service.encrypt("test_key")
        
        assert isinstance(result, str)

    def test_decrypt_roundtrip(self):
        """Encrypt then decrypt should return original plaintext"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        plaintext = "sk-ant-api03-test"
        
        ciphertext = service.encrypt(plaintext)
        decrypted = service.decrypt(ciphertext)
        
        assert decrypted == plaintext

    def test_same_plaintext_different_ciphertext(self):
        """Same plaintext should produce different ciphertext each time (random IV)"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        plaintext = "same_value"
        
        ciphertext1 = service.encrypt(plaintext)
        ciphertext2 = service.encrypt(plaintext)
        
        assert ciphertext1 != ciphertext2
        # But both should decrypt to same plaintext
        assert service.decrypt(ciphertext1) == plaintext
        assert service.decrypt(ciphertext2) == plaintext

    def test_decrypt_wrong_key_raises(self):
        """Decrypting with wrong key should raise EncryptionError"""
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()
        service1 = EncryptionService(key1)
        service2 = EncryptionService(key2)
        
        ciphertext = service1.encrypt("test_value")
        
        with pytest.raises(EncryptionError):
            service2.decrypt(ciphertext)

    def test_encrypt_empty_string_raises(self):
        """Encrypting empty string should raise EncryptionError"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        
        with pytest.raises(EncryptionError):
            service.encrypt("")

    def test_encrypt_none_raises(self):
        """Encrypting None should raise EncryptionError"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        
        with pytest.raises(EncryptionError):
            service.encrypt(None)

    def test_decrypt_tampered_ciphertext_raises(self):
        """Decrypting tampered ciphertext should raise EncryptionError"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        
        ciphertext = service.encrypt("valid_value")
        # Parse JSON and tamper with ciphertext
        payload = json.loads(ciphertext)
        tampered_payload = payload.copy()
        tampered_payload["ciphertext"] = payload["ciphertext"][:-1] + "X"
        tampered_ciphertext = json.dumps(tampered_payload)
        
        with pytest.raises(EncryptionError):
            service.decrypt(tampered_ciphertext)

    def test_decrypt_plaintext_raises(self):
        """Decrypting plaintext should raise EncryptionError"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        
        with pytest.raises(EncryptionError):
            service.decrypt("not_encrypted_text")

    # ── KEY VERSION TESTS ──

    def test_encrypted_value_has_version_field(self):
        """Encrypted value should have version field set to 1"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        
        result = service.encrypt("test")
        payload = json.loads(result)
        
        assert "v" in payload
        assert payload["v"] == 1

    def test_encrypted_value_has_ciphertext_field(self):
        """Encrypted value should have non-empty ciphertext field"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        
        result = service.encrypt("test")
        payload = json.loads(result)
        
        assert "ciphertext" in payload
        assert payload["ciphertext"]  # non-empty

    def test_decrypt_v1_format(self):
        """Should be able to decrypt valid v1 format manually constructed"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)
        
        # Create valid v1 format manually
        fernet = Fernet(key.encode())
        encrypted_bytes = fernet.encrypt("test_value".encode())
        v1_payload = {
            "v": 1,
            "ciphertext": encrypted_bytes.decode()
        }
        v1_json = json.dumps(v1_payload)
        
        decrypted = service.decrypt(v1_json)
        assert decrypted == "test_value"

    # ── CONFIG ERROR TESTS ──

    def test_raises_on_missing_encryption_key(self):
        """Should raise EncryptionConfigError when key is empty"""
        with pytest.raises(EncryptionConfigError):
            EncryptionService(key="")

    def test_raises_on_invalid_encryption_key(self):
        """Should raise EncryptionConfigError when key is invalid"""
        with pytest.raises(EncryptionConfigError):
            EncryptionService(key="not_a_valid_fernet_key")