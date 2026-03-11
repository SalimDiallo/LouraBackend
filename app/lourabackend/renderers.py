from rest_framework.renderers import JSONRenderer
from django.core.serializers.json import DjangoJSONEncoder


class UUIDJSONRenderer(JSONRenderer):
    """Custom JSON Renderer that handles UUIDs and other Django types"""
    encoder_class = DjangoJSONEncoder
