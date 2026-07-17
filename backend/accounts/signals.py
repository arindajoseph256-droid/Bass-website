from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    """Handle user creation."""
    if created:
        # Add welcome points
        instance.add_points(100)
        
        # Create user profile notification settings if needed
        pass


@receiver(pre_delete, sender=User)
def user_deleted(sender, instance, **kwargs):
    """Handle user deletion."""
    # Clean up related data if needed
    pass
