from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password

from common.serializers import *
from .models import *
from .utils import random_username, is_tel


# --------------------------------- 用户 ---------------------------------
# 创建用户
class UserCreateSerializer(ModelSerializer):
    def create(self, validated_data):
        if 'username' in validated_data:
            username = validated_data['username']
        else:
            username = random_username()
        # 使用create_user不是create
        instance = User.objects.create_user(username=username,
                                            tel=validated_data['tel'],
                                            password=validated_data['password'])
        return instance

    def validate_password(self, value):
        # 验证密码格式
        password_validation.validate_password(value)
        return value

    class Meta:
        model = User
        fields = ('username', 'tel', 'password')
        extra_kwargs = {'username': {'required': False}}


# 用户信息
class UserExpandSerializer(DynamicFieldsModelSerializer):
    password = serializers.CharField(max_length=128, required=False)

    def validate_password(self, value):
        if 'action' in self.context:
            if self.context['action'] == 'update':
                # 验证密码格式
                password_validation.validate_password(value)
                # 重新生成密码
                value = make_password(value)
        return value

    # 设置tel
    def validate_tel(self, value):
        if is_tel(value):
            return value
        else:
            raise serializers.ValidationError("请输入正确的手机号码")

    def create(self, validated_data):
        if 'username' in validated_data:
            username = validated_data.pop('username')
        else:
            username = random_username()

        user = User.objects.create_user(username=username, **validated_data)
        return user

    class Meta:
        model = User
        fields = ('username', 'password', 'gender', 'name', 'birth_day',
                  'tel', 'fixed_tel', 'qq', 'we_chat', 'contact_address',)
        extra_kwargs = {'username': {'required': False}}


# 列表用户
class UserListSerializer(DynamicFieldsModelSerializer):
    portrait = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'portrait', 'gender', 'get_gender_display', 'get_full_name')

    def get_portrait(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_portrait())


# 全部信息
class UserSerializer(DynamicFieldsModelSerializer):
    portrait = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ('password', 'is_superuser',)

    def get_portrait(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_portrait())


# 全部信息
class UserModifySerializer(DynamicFieldsModelSerializer):
    # 设置修改tel时返回400错误
    def validate_tel(self, value):
        if value:
            raise serializers.ValidationError("手机号码需要验证后才可修改")
        return value

    class Meta:
        model = User
        exclude = ('password', 'is_superuser',)
