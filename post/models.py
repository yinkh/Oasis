from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from common.utils import get_time_filename, validate_image_size, validate_video_size
from common.models import Base


def get_image_path(instance, filename):
    return 'image/{}'.format(get_time_filename(filename))


# 图片
class Image(models.Model):
    # 拥有者
    user = models.ForeignKey('user.User',
                             related_name='photo',
                             on_delete=models.CASCADE,
                             verbose_name='用户')
    image = models.ImageField(upload_to=get_image_path,
                              validators=[validate_image_size],
                              verbose_name='图片')
    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True,
                                       verbose_name='创建时间')

    class Meta:
        verbose_name = '图片'
        verbose_name_plural = '图片'

    def __str__(self):
        return '{} {}'.format(self.id, self.image.name)


def get_video_path(instance, filename):
    return 'video/{}'.format(get_time_filename(filename))


# 帖子
class Post(Base):
    # 用户
    user = models.ForeignKey('user.User',
                             related_name='deed',
                             on_delete=models.CASCADE,
                             verbose_name=u'用户')
    # 状态
    STATUS = {
        0: u'公开',
        1: u'好友可见',
        2: u'仅我可见',
    }
    status = models.PositiveIntegerField(choices=STATUS.items(),
                                         default=0,
                                         verbose_name=u'状态')
    # 标题
    title = models.CharField(max_length=100,
                             verbose_name=u'标题')
    # 详情
    content = models.TextField(null=True,
                               verbose_name=u'详情')
    # 类型
    CATEGORY = {
        0: u'视频',
        1: u'图片',
    }
    category = models.PositiveIntegerField(choices=CATEGORY.items(),
                                           verbose_name=u'类型')
    # 视频
    video = models.FileField(upload_to=get_video_path,
                             validators=[validate_video_size],
                             blank=True,
                             verbose_name=u'视频')
    # 图片
    images = models.ManyToManyField('post.Image',
                                    blank=True,
                                    verbose_name='图片')
    # 时间
    time = models.DateTimeField(null=True,
                                default=timezone.now,
                                verbose_name='时间')
    # 地点-名称
    place = models.CharField(max_length=255,
                             null=True,
                             blank=True,
                             verbose_name='地点-名称')
    # 地点-经纬度
    location = models.CharField(max_length=30,
                                null=True,
                                blank=True,
                                verbose_name='地点-经纬度')

    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = '帖子'

    # def clean(self):
    #     images = self.cleaned_data.get('images')
    #     print(images)
    #     if self.category == 0 and self.images.count() != 0:
    #         raise ValidationError({'images': '视频不接收多图'})
    #     elif self.category == 1 and self.video:
    #         raise ValidationError({'video': '多图不接收视频'})

    def __str__(self):
        return '{} {}'.format(self.id, self.title)
