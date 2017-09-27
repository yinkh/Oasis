from django.db import models

from common.models import Base


# 关注
class Follow(Base):
    # 关注人
    from_user = models.ForeignKey('user.User',
                                  related_name='follow_from_user',
                                  on_delete=models.CASCADE,
                                  verbose_name=u'关注人')
    # 被关注人
    to_user = models.ForeignKey('user.User',
                                related_name='follow_to_user',
                                on_delete=models.CASCADE,
                                verbose_name=u'被关注人')

    class Meta:
        verbose_name = '关注'
        verbose_name_plural = '关注'

    def __str__(self):
        return '{} {}'.format(self.from_user.username, self.to_user.username)
