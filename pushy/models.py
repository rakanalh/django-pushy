from django.db import models
from django.contrib.auth import get_user_model
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

    active = models.SmallIntegerField(choices=PUSH_CHOICES, default=PUSH_ACTIVE)
    sent = models.SmallIntegerField(choices=PUSH_SENT_CHOICES, default=PUSH_NOT_SENT)

    date_created = models.DateTimeField(auto_now_add=True)

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
    user = models.ForeignKey(get_user_model(), blank=True, null=True)

    class Meta:
        unique_together = ('key', 'type')