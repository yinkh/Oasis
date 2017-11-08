from django.db import models
from django.utils import timezone

from common.models import Base


# 推荐
class Recommend(Base):
    # 用户
    user = models.ForeignKey('user.User',
                             on_delete=models.CASCADE,
                             related_name='recommend_user',
                             verbose_name=u'发布人')
    # 帖子
    posts = models.ManyToManyField('post.Post',
                                   verbose_name=u'帖子')
    # 日期
    date = models.DateField(unique=True,
                            default=timezone.now,
                            verbose_name=u'日期')

    class Meta:
        verbose_name = '推荐'
        verbose_name_plural = '推荐'
        ordering = ('-id',)

    def __str__(self):
        return '{} {}'.format(self.user.get_full_name(), self.date)
