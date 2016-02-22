from pushy.models import Device
from rest_framework import serializers


def get_types_map():
    return {
        device_type[1].lower(): device_type[0]
        for device_type in Device.DEVICE_TYPE_CHOICES
    }


class DeviceSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=get_types_map(), required=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate_type(self, value):
        types_map = get_types_map()
        return types_map[value]

    class Meta:
        model = Device
        fields = ('key', 'type', 'user')
