from django.conf.urls import url

from .views import DeviceViewSet

urlpatterns = [
    url(r'^pushy/device/$',
        DeviceViewSet.as_view({
            'post': 'create',
            'delete': 'destroy'
        }),
        name='pushy-devices'),
]
