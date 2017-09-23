from django.db import models

from common.models import Base
from common.constants import FriendState


# 好友关系
class Friend(Base):
    # 好友关系起始人
    from_user = models.ForeignKey('user.User',
                                  related_name='friend_from_user',
                                  on_delete=models.CASCADE,
                                  verbose_name=u'关系起始人')
    # 好友关系结束人
    to_user = models.ForeignKey('user.User',
                                related_name='friend_to_user',
                                on_delete=models.CASCADE,
                                verbose_name=u'关系结束人')
    # 当前好友状态选项
    STATE = {
        FriendState.Pending: u'待处理',
        FriendState.Accept: u'已接受',
        FriendState.Reject: u'已拒绝',
    }
    # 当前好友状态
    state = models.IntegerField(choices=STATE.items(),
                                verbose_name=u'好友状态')
    # 黑名单
    is_block = models.BooleanField(default=False,
                                   verbose_name=u'黑名单')
    # 备注名称
    remark = models.CharField(max_length=255,
                              blank=True,
                              verbose_name=u'备注名称')
    # 验证消息
    say_hi = models.CharField(max_length=255,
                              blank=True,
                              verbose_name=u'验证消息')

    class Meta:
        verbose_name = '好友关系'
        verbose_name_plural = '好友关系'

    def __str__(self):
        return '{} {}'.format(self.from_user.username, self.to_user.username)
