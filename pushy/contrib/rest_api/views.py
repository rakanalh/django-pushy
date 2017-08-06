from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings

from pushy.models import Device

from .serializers import DeviceSerializer


class DeviceViewSet(viewsets.ViewSet):
    def create(self, request):
        serializer = DeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user_id=request.user.id)

        return Response(
            request.data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request):
        try:
            key = request.data.get('key', None)
            Device.objects.get(key=key).delete()

            return Response(
                request.data,
                status=status.HTTP_200_OK
            )
        except Device.DoesNotExist:
            return self._not_found_response(key)

    def _not_found_response(self, key):
        errors_key = api_settings.NON_FIELD_ERRORS_KEY

        return Response(data={
            errors_key: ['Key {} was not found'.format(key)]
        }, status=status.HTTP_404_NOT_FOUND)
