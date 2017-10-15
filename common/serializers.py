from collections import OrderedDict
from rest_framework import serializers
from rest_framework.fields import SkipField


# 将None序列化为 '' 而不是 'null'
class ModelSerializer(serializers.ModelSerializer):
    def build_field(self, field_name, info, model_class, nested_depth):
        """
        Return a two tuple of (cls, kwargs) to build a serializer field with.

        重新该方法以保证model中Field在null=True的情况下依旧是必填项
        field_kwargs中required参数原始判断依据
        (build_field->build_standard_field \ build_relational_field->get_field_kwargs\get_relation_kwargs):
            if model_field.has_default() or model_field.blank or model_field.null:
                kwargs['required'] = False
        更新后依据:
            if model_field.has_default() or model_field.blank:
                field_kwargs['required'] = False
            else:
                field_kwargs['required'] = True
        """
        if field_name in info.fields_and_pk:
            # 普通field 部分
            model_field = info.fields_and_pk[field_name]
            field_class, field_kwargs = self.build_standard_field(field_name, model_field)
            field_kwargs['required'] = False if (model_field.has_default() or model_field.blank) else True
            return field_class, field_kwargs

        elif field_name in info.relations:
            # FK\M2M 部分
            relation_info = info.relations[field_name]

            if not nested_depth:
                field_class, field_kwargs = self.build_relational_field(field_name, relation_info)
                model_field, related_model, to_many, to_field, has_through_model, reverse = relation_info
                field_kwargs['required'] = False if (model_field.has_default() or model_field.blank) else True
                return field_class, field_kwargs
            else:
                return self.build_nested_field(field_name, relation_info, nested_depth)

        elif hasattr(model_class, field_name):
            return self.build_property_field(field_name, model_class)

        elif field_name == self.url_field_name:
            return self.build_url_field(field_name, model_class)

        return self.build_unknown_field(field_name, model_class)

    def to_representation(self, instance):
        """
              Object instance -> Dict of primitive data types.
        """
        ret = OrderedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            try:
                key = field.get_attribute(instance)
            except SkipField:
                continue
            if key is not None:
                value = field.to_representation(key)
                # 子对象中有对象为空 依旧序列化
                if value is None:
                    value = ''
                # 子对象中有列表为空 依旧序列化 eg:Moment->photos为空依旧要序列化
                # if isinstance(value, list) and not value:
                #     # Do not serialize empty lists
                #     print('empty lists')
                #     continue
                ret[field.field_name] = value
                # print(field.field_name, value)
            else:
                # value None to '' rather tan 'null'
                # print(field.field_name, field.to_representation(key), '有空值')
                ret[field.field_name] = ''

        # 为serializers中动态添加的context赋值输出
        for field in self.context:
            # context defaults to including 'request', 'view' and 'format' keys.
            if field not in ['request', 'view', 'format']:
                ret[field] = self.context[field]
        return ret


# 动态获取Fields
class DynamicFieldsModelSerializer(ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            not_allowed = set(exclude)
            for exclude_name in not_allowed:
                self.fields.pop(exclude_name)