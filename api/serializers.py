from rest_framework import serializers
from core.models import Link, Click


class LinkSerializer(serializers.ModelSerializer):
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = Link
        fields = [
            'id', 'short_code', 'custom_slug', 'original_url', 'title',
            'is_active', 'click_count', 'short_url', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'short_code', 'click_count', 'short_url', 'created_at', 'updated_at']

    def get_short_url(self, obj):
        return obj.get_short_url()


class LinkCreateSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=2048)
    custom_slug = serializers.CharField(max_length=100, required=False, allow_blank=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class LinkUpdateSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2048, required=False)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    custom_slug = serializers.CharField(max_length=100, required=False, allow_blank=True)


class ClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = Click
        fields = [
            'id', 'clicked_at', 'referrer', 'country', 'city',
            'device_type', 'browser', 'os',
        ]


class BulkCreateItemSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=2048)
    custom_slug = serializers.CharField(max_length=100, required=False, allow_blank=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class BulkCreateSerializer(serializers.Serializer):
    links = BulkCreateItemSerializer(many=True, max_length=100)
