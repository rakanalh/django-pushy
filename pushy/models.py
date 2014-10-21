import json
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class PushNotification(models.Model):
    PUSH_INACTIVE = 0
    PUSH_ACTIVE = 1

    PUSH_NOT_SENT = 0
    PUSH_SENT = 1

    PUSH_CHOICES = (
        (PUSH_ACTIVE, _('Active')),
        (PUSH_INACTIVE, _('Inactive'))
    )

    PUSH_SENT_CHOICES = (
        (PUSH_NOT_SENT, _('Not Sent')),
        (PUSH_SENT, _('Sent'))
    )

    title = models.CharField(max_length=50)
    body = models.TextField()

    active = models.SmallIntegerField(choices=PUSH_CHOICES,
                                      default=PUSH_ACTIVE)
    sent = models.SmallIntegerField(choices=PUSH_SENT_CHOICES,
                                    default=PUSH_NOT_SENT)

    date_created = models.DateTimeField(auto_now_add=True)

    filter_type = models.SmallIntegerField(blank=True, default=0)
    filter_user = models.IntegerField(blank=True, default=0)

    @property
    def payload(self):
        if self.body:
            return json.loads(self.body)
        return None

    @payload.setter
    def payload(self, value):
        self.body = json.dumps(value)

    def __unicode__(self):
        return self.title


class Device(models.Model):
    DEVICE_TYPE_ANDROID = 1
    DEVICE_TYPE_IOS = 2
    DEVICE_TYPE_CHOICES = (
        (DEVICE_TYPE_ANDROID, _('Android')),
        (DEVICE_TYPE_IOS, _('iOS'))
    )

    key = models.TextField()
    type = models.SmallIntegerField(choices=DEVICE_TYPE_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)


def get_filtered_devices_queryset(notification):
    devices = Device.objects.all()

    if notification.filter_type:
        devices = devices.filter(type=notification.filter_type)
    if notification.filter_user:
        devices = devices.filter(user_id=notification.filter_user)

    return devices
