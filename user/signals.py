from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import *


# 生成Im Token
@receiver(post_save, sender=User)
def create_im_token(sender, instance=None, created=False, **kwargs):
    if created:
        instance.refresh_im_token()
