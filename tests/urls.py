from django.conf.urls import include, url
from django.contrib import admin

from pushy.contrib.rest_api import urls as rest_urls

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(rest_urls))
]
