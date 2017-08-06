import datetime
import logging

import celery

from django.conf import settings
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone

from .models import (
    PushNotification,
    Device,
    get_filtered_devices_queryset
)
from .exceptions import (
    PushInvalidTokenException,
    PushException
)
from .dispatchers import get_dispatcher


logger = logging.getLogger(__name__)


@celery.shared_task(
    queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', None)
)
def check_pending_push_notifications():
    pending_notifications = PushNotification.objects.filter(
        sent=PushNotification.PUSH_NOT_SENT
    )

    for pending_notification in pending_notifications:
        create_push_notification_groups.apply_async(kwargs={
            'notification': pending_notification.to_dict()
        })


@celery.shared_task(
    queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', None)
)
def create_push_notification_groups(notification):
    devices = get_filtered_devices_queryset(notification)

    date_started = timezone.now()

    if devices.count() > 0:
        count = devices.count()
        limit = getattr(settings, 'PUSHY_DEVICE_KEY_LIMIT', 1000)
        celery.chord(
            send_push_notification_group.s(notification, offset, limit)
            for offset in range(0, count, limit)
        )(notify_push_notification_sent.si(notification))

    if not notification['id']:
        return

    try:
        notification = PushNotification.objects.get(pk=notification['id'])
        notification.sent = PushNotification.PUSH_IN_PROGRESS
        notification.date_started = date_started
        notification.save()
    except PushNotification.DoesNotExist:
        return


@celery.shared_task(
    queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', None)
)
def send_push_notification_group(notification, offset=0, limit=1000):
    devices = get_filtered_devices_queryset(notification)

    devices = devices[offset:offset + limit]

    for device in devices:
        send_single_push_notification(device, notification['payload'])

    return True


@celery.shared_task(
    queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', None)
)
def send_single_push_notification(device, payload):
    # The task can be called in two ways:
    # 1) from send_push_notification_group directly with a device instance
    # 2) As a task using .delay or apply_async with a device id
    if isinstance(device, int):
        try:
            device = Device.objects.get(pk=device)
        except Device.DoesNotExist:
            return False

    dispatcher = get_dispatcher(device.type)

    try:
        canonical_id = dispatcher.send(device.key, payload)
        if not canonical_id:
            return

        with transaction.atomic():
            device.key = canonical_id
            device.save()

    except IntegrityError:
        device.delete()
    except PushInvalidTokenException:
        logger.debug('Token for device {} does not exist, skipping'.format(
            device.id
        ))
        device.delete()
    except PushException:
        logger.exception("An error occured while sending push notification")
        return


@celery.shared_task(
    queue=getattr(settings, 'PUSH_QUEUE_DEFAULT_NAME', None),
)
def notify_push_notification_sent(notification):
    if not notification['id']:
        return False

    try:
        notification = PushNotification.objects.get(pk=notification['id'])
        notification.date_finished = timezone.now()
        notification.sent = PushNotification.PUSH_SENT
        notification.save()
    except PushNotification.DoesNotExist:
        logger.exception("Notification {} does not exist".format(notification))
        return False


@celery.shared_task(
    queue=getattr(settings, 'PUSH_QUEUE_DEFAULT_NAME', None)
)
def clean_sent_notifications():
    max_age = getattr(settings, 'PUSHY_NOTIFICATION_MAX_AGE', None)

    if not max_age or not isinstance(max_age, datetime.timedelta):
        raise ValueError('Notification max age value is not defined.')

    delete_before_date = timezone.now() - max_age
    PushNotification.objects.filter(
        sent=PushNotification.PUSH_SENT,
        date_finished__lt=delete_before_date
    ).delete()
