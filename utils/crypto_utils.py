from cryptography.fernet import Fernet

# Use the same key for encryption/decryption (save it securely)
SECRET_KEY = b'Z_Ho9CFBxSKuZfFpm9ueyXWm8A61FezCkUvbFDhi6n4='  # <- Save this, generate only once
fernet = Fernet(SECRET_KEY)

def encrypt_uid(uid: str) -> str:
    return fernet.encrypt(uid.encode()).decode()

def decrypt_uid(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()
