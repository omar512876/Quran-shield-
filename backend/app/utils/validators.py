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


ALLOWED_AUDIO_MIMES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/ogg", "audio/mp4", "audio/x-m4a", "audio/aac",
    "audio/flac", "audio/webm", "video/mp4", "video/webm",
    "application/octet-stream"
}


def validate_audio_mime(content_type: str) -> bool:
    """
    Validate that a content type is an allowed audio MIME type.
    
    Args:
        content_type: The MIME type string to validate
        
    Returns:
        True if content_type is in the allowed set, False otherwise
    """
    if not content_type:
        return False
    return content_type.lower().split(";")[0].strip() in ALLOWED_AUDIO_MIMES


ALLOWED_YOUTUBE_HOSTS = {
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"
}


def validate_youtube_url(url: str) -> bool:
    """
    Validate that a URL is from an allowed YouTube domain.
    
    Args:
        url: The URL string to validate
        
    Returns:
        True if the URL hostname is a valid YouTube domain, False otherwise
    """
    try:
        result = urlparse(url)
        hostname = result.hostname
        if hostname is None:
            return False
        return hostname.lower() in ALLOWED_YOUTUBE_HOSTS
    except (ValueError, AttributeError):
        return False
