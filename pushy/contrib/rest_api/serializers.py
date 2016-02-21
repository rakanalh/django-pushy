from pushy.models import Device
from rest_framework import serializers


class DeviceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Device
        fields = ('key', 'type', 'user')
