import re
from django.core.exceptions import ValidationError


def validate_file_size(file, max_size_mb=10):
    """Validate file size in MB."""
    file_size = file.size
    limit_mb = max_size_mb
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"File size cannot exceed {limit_mb}MB.")


def validate_image_file(file):
    """Validate image file types."""
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    extension = str(file.name).lower().split(".")[-1]
    if f".{extension}" not in allowed_extensions:
        raise ValidationError(f"Unsupported file extension. Allowed: {', '.join(allowed_extensions)}")


def validate_pdf_file(file):
    """Validate PDF file."""
    if not str(file.name).lower().endswith(".pdf"):
        raise ValidationError("Only PDF files are allowed.")


def validate_video_file(file):
    """Validate video file types."""
    allowed_extensions = [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"]
    extension = str(file.name).lower().split(".")[-1]
    if f".{extension}" not in allowed_extensions:
        raise ValidationError(f"Unsupported video extension. Allowed: {', '.join(allowed_extensions)}")


def validate_document_file(file):
    """Validate document file types."""
    allowed_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"]
    extension = str(file.name).lower().split(".")[-1]
    if f".{extension}" not in allowed_extensions:
        raise ValidationError(f"Unsupported document extension. Allowed: {', '.join(allowed_extensions)}")


def validate_username(username):
    """Validate username format."""
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValidationError("Username can only contain letters, numbers, and underscores.")
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long.")
    if len(username) > 30:
        raise ValidationError("Username cannot exceed 30 characters.")


def validate_password_strength(password):
    """Validate password meets strength requirements."""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one number.")


def validate_no_html_tags(value):
    """Validate that value doesn't contain HTML tags."""
    if re.search(r"<[^>]+>", str(value)):
        raise ValidationError("HTML tags are not allowed.")
