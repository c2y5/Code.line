import os
from hashlib import sha256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def _normalize_key(key):
    if isinstance(key, str):
        key = key.encode("utf-8")
    return sha256(key).digest()

def aes_encrypt(input_bytes, key):
    key = _normalize_key(key)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(input_bytes) + encryptor.finalize()
    return iv + encrypted

def aes_decrypt(encrypted_bytes, key):
    key = _normalize_key(key)
    iv = encrypted_bytes[:16]
    actual_encrypted = encrypted_bytes[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(actual_encrypted) + decryptor.finalize()
