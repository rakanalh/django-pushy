from django.conf.urls import patterns, url

import views

urlpatterns = patterns(
    '',
    url(r'^pushy/device/$',
        views.DeviceViewSet.as_view({
            'post': 'create',
            'delete': 'destroy'
        }),
        name='pushy-devices'),
)
