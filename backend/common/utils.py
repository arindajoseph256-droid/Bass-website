import uuid
import os
from django.utils.text import slugify
from django.core.files.storage import default_storage


def generate_unique_slug(instance, base_slug, max_length=100):
    """Generate a unique slug for a model instance."""
    slug = slugify(base_slug)[:max_length]
    model_class = instance.__class__
    unique_slug = slug
    counter = 1

    while model_class.objects.filter(slug=unique_slug).exclude(pk=instance.pk).exists():
        unique_slug = f"{slug}-{counter}"
        counter += 1

    return unique_slug


def generate_uuid():
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def get_file_extension(filename):
    """Get the file extension from a filename."""
    return os.path.splitext(filename)[1].lower()


def validate_file_type(file, allowed_types):
    """Validate file type against allowed types."""
    extension = get_file_extension(file.name)
    return extension in allowed_types


def upload_to(instance, filename, directory="uploads"):
    """Generate upload path for files."""
    ext = get_file_extension(filename)
    new_filename = f"{generate_uuid()}{ext}"
    return os.path.join(directory, new_filename)


def format_datetime(dt):
    """Format datetime for API responses."""
    if dt:
        return dt.isoformat()
    return None


def calculate_percentage(part, total):
    """Calculate percentage with division by zero handling."""
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
