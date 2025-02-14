import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from server.steganography.steganography_errors import ContentWrapperError


def encrypt(plaintext: bytes, key: bytes) -> tuple[bytes, bytes, bytes, bytes, bytes]:
    """
    Encrypts plaintext using AES-256 GCM algorithm.
    :param plaintext: the plaintext to be encrypted
    :param key: the encryption key
    :return: the encrypted ciphertext, with the relevant info in the form of: ciphertext, tag, nonce, header, key
    """
    key_hash = hashlib.sha256(key).digest()
    update_header = get_random_bytes(8)
    cipher = AES.new(key_hash, AES.MODE_GCM, mac_len=16)
    cipher.update(update_header)
    ciphertext, verification_tag = cipher.encrypt_and_digest(plaintext)
    return ciphertext, verification_tag, cipher.nonce, update_header, key


def decrypt(ciphertext: bytes, key: bytes, tag: bytes, nonce: bytes, update_header: bytes) -> bytes:
    """
    Decrypts ciphertext using AES-256 GCM algorithm.
    :param ciphertext: the ciphertext to be decrypted
    :param key: the encryption key
    :param tag: the GCM tag
    :param nonce: the GCM nonce
    :param update_header: the GCM header
    :return: the decrypted plaintext
    :raises ContentWrapperError: if the decryption process fails
    """
    key_hash = hashlib.sha256(key).digest()
    cipher = AES.new(key_hash, AES.MODE_GCM, mac_len=16, nonce=nonce)
    try:
        cipher.update(update_header)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    except (ValueError, KeyError) as e:
        # something went wrong with the decryption process (tampered or incorrect data)
        raise ContentWrapperError(f"Data decryption was unsuccessful. {e}")
    return plaintext
