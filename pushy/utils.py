from models import PushNotification
from pushy.tasks import send_single_push_notification
from tasks import create_push_notification_groups


def send_push_notification(title, payload, device=None,
                           filter_user=None, filter_type=None):

    notification = PushNotification.objects.create(
        title=title,
        payload=payload,
        active=PushNotification.PUSH_ACTIVE,
        sent=PushNotification.PUSH_NOT_SENT
    )

    if device:
        # Send a single push notification immediately
        send_single_push_notification.apply_async(kwargs={
            'device': device.id,
            'payload': notification.payload
        })
        return

    if filter_type or filter_user:
        if filter_user:
            notification.filter_user = filter_user.id
        if filter_type:
            notification.filter_type = filter_type
        notification.save()

    create_push_notification_groups.delay(notification_id=notification.id)
