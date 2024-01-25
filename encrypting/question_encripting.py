from cryptography.fernet import Fernet

from encrypting.key_init import key

f = Fernet(key)


def decrypt_bytes(b: bytes) -> str:
    return f.decrypt(b).decode()


def encrypt_text(text: str) -> bytes:
    return f.encrypt(text.encode())
