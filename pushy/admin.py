import json
from django.contrib import admin
from django import forms

from .models import PushNotification, Device


class PushNotificationForm(forms.ModelForm):
    def clean(self):
        body = self.cleaned_data.get('body')
        try:
            body = json.loads(body)
        except ValueError:
            raise forms.ValidationError('Body does not contain valid JSON')
        return self.cleaned_data

    class Meta:
        model = PushNotification
        fields = (
            'title', 'body', 'active', 'sent', 'filter_type', 'filter_user'
        )


class PushNotificationAdmin(admin.ModelAdmin):
    form = PushNotificationForm
    list_display = (
        'title',
        'date_created',
        'active',
        'sent',
        'date_started',
        'date_finished'
    )
    list_filter = ('active', 'sent')
    search_fields = ('title', )
    readonly_fields = ('date_started', 'date_finished')


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('key', )
    list_filter = ('user', )


admin.site.register(PushNotification, PushNotificationAdmin)
admin.site.register(Device, DeviceAdmin)
