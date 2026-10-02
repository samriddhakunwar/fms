from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, sync_role_profile


@receiver(post_save, sender=User)
def keep_role_profile_in_sync(sender, instance, raw=False, **kwargs):
    # Covers every way an account is saved — the API, Django admin and
    # createsuperuser — so an Admin/Manager never exists without its record.
    if raw:
        return
    sync_role_profile(instance)
