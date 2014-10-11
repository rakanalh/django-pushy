from django.conf import settings
from celery import task, group

from ..models import PushNotification, Device
from ..dispatchers import get_dispatcher, Dispatcher


@task(queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', 'default'))
def check_pending_push_notifications():
    pending_notifications = PushNotification.objects.filter(
        sent=PushNotification.PUSH_NOT_SENT)

    for pending_notification in pending_notifications:
        create_push_notification_groups.apply_async(
            kwargs={'notification_id': pending_notification.id})

        pending_notification.sent = PushNotification.PUSH_SENT
        pending_notification.save()


@task(queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', 'default'))
def create_push_notification_groups(notification_id):
    devices = Device.objects.all()

    if devices.count() > 0:
        count = devices.count()
        limit = getattr(settings, 'PUSHY_DEVICE_KEY_LIMIT', 1000)
        group(send_push_notification_group.s(
            notification_id, offset, limit)
            for offset in range(0, count, limit)).delay()


@task(queue=getattr(settings, 'PUSHY_QUEUE_DEFAULT_NAME', 'default'))
def send_push_notification_group(notification_id, offset=0, limit=1000):
    try:
        notification = PushNotification.objects.get(pk=notification_id)
    except PushNotification.DoesNotExist:
        return False

    data = {
        'title': notification.title,
        'body': notification.body
    }

    keys = Device.objects.all()[offset:offset+limit]

    for key in keys:
        dispatcher = get_dispatcher(key.type)

        result, canonical_id = dispatcher.send(key.key, data)

        if result == Dispatcher.PUSH_RESULT_SENT:
            if canonical_id > 0:
                key.key = canonical_id
                key.save()
        elif result == Dispatcher.PUSH_RESULT_NOT_REGISTERED:
            key.delete()

    return True
