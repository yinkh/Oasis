from django.db import models

from common.models import Base


class Favorites(Base):
    # 用户
    user = models.ForeignKey('user.User',
                             related_name='favorites_user',
                             on_delete=models.CASCADE,
                             verbose_name=u'用户')
    # 名称
    name = models.CharField(max_length=255,
                            null=True,
                            verbose_name=u'名称')
    # 封面
    cover = models.ForeignKey('user.File',
                              related_name='favorites_cover',
                              null=True,
                              verbose_name=u'封面')
    # 类型
    CATEGORY = {
        0: u'公开',
        1: u'私有',
    }
    category = models.PositiveIntegerField(choices=CATEGORY.items(),
                                           verbose_name=u'类型')
    # 帖子
    posts = models.ManyToManyField('post.Post',
                                   blank=True,
                                   verbose_name='帖子')

    class Meta:
        verbose_name = '收藏夹'
        verbose_name_plural = '收藏夹'

    # 帖子总数
    def get_posts_count(self):
        return self.posts.count()

    def __str__(self):
        return '{} {}'.format(self.id, self.name)
