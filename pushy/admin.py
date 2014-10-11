from django.contrib import admin
from models import PushNotification, Device


class PushNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_created', 'active', 'sent')
    list_filter = ('active', 'sent')
    search_fields = ('title', )


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('key', )
    list_filter = ('user', )


admin.site.register(PushNotification, PushNotificationAdmin)
admin.site.register(Device, DeviceAdmin)
