from django.conf import settings
import celery

from ..models import PushNotification
from ..dispatchers import get_dispatcher, Dispatcher
from pushy.models import get_filtered_devices_queryset, Device


@celery.shared_task(
    queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', None)
)
def check_pending_push_notifications():
    pending_notifications = PushNotification.objects.filter(
        sent=PushNotification.PUSH_NOT_SENT)

    for pending_notification in pending_notifications:
        create_push_notification_groups.apply_async(
            kwargs={'notification_id': pending_notification.id})

        pending_notification.sent = PushNotification.PUSH_SENT
        pending_notification.save()


@celery.shared_task(
    queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', None)
)
def create_push_notification_groups(notification_id):
    try:
        notification = PushNotification.objects.get(pk=notification_id)
    except PushNotification.DoesNotExist:
        return False

    devices = get_filtered_devices_queryset(notification)

    if devices.count() > 0:
        count = devices.count()
        limit = getattr(settings, 'PUSHY_DEVICE_KEY_LIMIT', 1000)
        celery.group(send_push_notification_group.s(
            notification_id, offset, limit)
            for offset in range(0, count, limit)).delay()


@celery.shared_task(
    queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', None)
)
def send_push_notification_group(notification_id, offset=0, limit=1000):
    try:
        notification = PushNotification.objects.get(pk=notification_id)
    except PushNotification.DoesNotExist:
        return False

    devices = get_filtered_devices_queryset(notification)

    devices = devices[offset:offset+limit]

    for device in devices:
        send_single_push_notification(device, notification.payload)

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

    result, canonical_id = dispatcher.send(device.key, payload)

    if result == Dispatcher.PUSH_RESULT_SENT:
        if canonical_id > 0:
            device.key = canonical_id
            device.save()
    elif result == Dispatcher.PUSH_RESULT_NOT_REGISTERED:
        device.delete()

    return True
