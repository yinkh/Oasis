from django.conf import settings
from django.dispatch import receiver
from constance.signals import config_updated
from common.utils import get_value

# 预加载敏感词
sensitive_words = list(set(get_value(settings.SENSITIVE_WORD).replace('，', ',').split(',')))


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    if key == settings.SENSITIVE_WORD:
        # 更新全局敏感词
        global sensitive_words
        # 去重
        sensitive_words = list(set(new_value.replace('，', ',').split(',')))
