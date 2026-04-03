"""Input validation utilities"""
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Validate that a string is a properly formatted HTTP/HTTPS URL.
    
    Args:
        url: The URL string to validate
        
    Returns:
        True if valid HTTP/HTTPS URL, False otherwise
    """
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except (ValueError, AttributeError):
        return False
