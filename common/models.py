from django.db import models


# 未被删除的管理器
class PublicManager(models.Manager):
    def get_queryset(self):
        return super(PublicManager, self).get_queryset().filter(is_abandon=False)


# 基类
class Base(models.Model):
    # 是否删除
    is_abandon = models.BooleanField(default=False,
                                     verbose_name=u'是否删除')
    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True,
                                       verbose_name=u'创建时间')
    # 更新时间
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name=u'更新时间')

    objects = PublicManager()
    all = models.Manager()

    class Meta:
        abstract = True
