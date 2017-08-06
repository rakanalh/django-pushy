from .models import PushNotification
from .tasks import (
    send_single_push_notification,
    create_push_notification_groups
)


def send_push_notification(title, payload, device=None,
                           filter_user=None, filter_type=None,
                           store=True):

    if not filter_type:
        filter_type = 0
    if not filter_user:
        filter_user = 0

    notification = PushNotification(
        title=title,
        payload=payload,
        active=PushNotification.PUSH_ACTIVE,
        sent=PushNotification.PUSH_NOT_SENT,
        filter_user=filter_user,
        filter_type=filter_type
    )
    if store:
        notification.save()

    if device:
        # Send a single push notification immediately
        send_single_push_notification.apply_async(kwargs={
            'device': device.id,
            'notification': notification.to_dict()
        })
        return notification

    create_push_notification_groups.delay(notification=notification.to_dict())

    return notification
