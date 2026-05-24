import base64
import hashlib

from cryptography.fernet import Fernet


def _get_fernet(secret: str, user_id: str) -> Fernet:
    key_material = f"{secret}:{user_id}".encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
    return Fernet(key)


def encrypt_for_user(plaintext: str, user_id: str, secret: str) -> str:
    f = _get_fernet(secret, user_id)
    return f.encrypt(plaintext.encode()).decode()


def decrypt_for_user(ciphertext: str, user_id: str, secret: str) -> str:
    f = _get_fernet(secret, user_id)
    return f.decrypt(ciphertext.encode()).decode()
