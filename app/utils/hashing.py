import hashlib


def calculate_sha256(content: bytes) -> str:
    """Calculate the SHA256 hex checksum of bytes content."""
    return hashlib.sha256(content).hexdigest()

def calculate_sha256_string(text: str) -> str:
    """Calculate the SHA256 hex checksum of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
