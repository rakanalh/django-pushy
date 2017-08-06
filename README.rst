django-pushy
============
Your push notifications handled at scale.

.. image:: https://travis-ci.org/rakanalh/django-pushy.svg?branch=master
    :target: https://travis-ci.org/rakanalh/django-pushy
.. image:: https://coveralls.io/repos/rakanalh/django-pushy/badge.png?branch=master
  :target: https://coveralls.io/r/rakanalh/django-pushy?branch=master
.. image:: https://landscape.io/github/rakanalh/django-pushy/master/landscape.svg?style=flat
   :target: https://landscape.io/github/rakanalh/django-pushy/master
   :alt: Code Health

What does it do?
----------------
Python / Django app that provides push notifications functionality with celery. The main purpose of this app is to help you send push notifications to your users at scale. If you have lots of registered device keys, django-pushy will split your keys into smaller groups which run in parallel making the process of sending notifications faster.

Setup
-----
You can install the library directly from pypi using pip::

    $ pip install django-pushy


Add django-pushy to your INSTALLED_APPS::

    INSTALLED_APPS = (
        ...
        "djcelery",
        "pushy"
    )

Configurations::

    # Android
    PUSHY_GCM_API_KEY = 'YOUR_API_KEY_HERE'

    # Send JSON or plaintext payload to GCM server (default is JSON)
    PUSHY_GCM_JSON_PAYLOAD = True

    # iOS
    PUSHY_APNS_SANDBOX = True or False
    PUSHY_APNS_CERTIFICATE_FILE = 'PATH_TO_CERTIFICATE_FILE'

    PUSHY_QUEUE_DEFAULT_NAME = 'default'
    PUSHY_DEVICE_KEY_LIMIT = 1000


Run DB migrations::

    python manage.py migrate

How do i use it?
----------------

There are 2 models provided by Pushy:
1) PushNotification
2) Device

You have to implement your own code to use the Device model to register keys into the database::

    from pushy.models import Device
    Device.objects.create(key='123', type=Device.DEVICE_TYPE_ANDROID, user=current_user)
    Device.objects.create(key='123', type=Device.DEVICE_TYPE_IOS, user=None)


Whenever you need to push a notification, use the following code::

    from pushy.utils import send_push_notification
    send_push_notification('Push_Notification_Title', {'key': 'value' ...})

This will send a push notification to all registered devices.
You can also send a single notification to a single device::

    device = Device.objects.get(pk=1)
    send_push_notification('YOUR TITLE', {YOUR_PAYLOAD}, device=device)


Or you can use the filter_user or filter_type to make pushy send to a specified queryset of devices::

    send_push_notification('YOUR TITLE', {YOUR_PAYLOAD}, filter_user=user)
    send_push_notification('YOUR TITLE', {YOUR_PAYLOAD}, filter_type=Device.DEVICE_TYPE_IOS)

If you don't want to store the push notification into the database, you could pass in a keyword argument::

  send_push_notification('YOUR_TITLE', {YOUR_PAYLOAD}, device=device, store=False)

If you would like to add a push notification without triggering any action right away, you should be setting the property "payload
instead of adding your dict to body as follows::

    notification = PushNotification.objects.create(
        title=title,
        payload=payload,
        active=PushNotification.PUSH_ACTIVE,
        sent=PushNotification.PUSH_NOT_SENT
    )

As some serialization takes place to automatically convert the payload to a JSON string to be stored into the database.

**iOS Users Note:**
Please note that iOS special parameters: alert, sound, badge, content-available are all preset for you to None/False. Django-pushy ads payload you provide to the custom payload field.


Restful APIs
------------

To use Restful APIs, pushy requires DRF >= 3.0.::

    pip install django-pushy[apis]


And add the following to your urls.py::

    from pushy.contrib.rest_api import urls as pushy_rest_urls

    urlpatterns += [
        url(r'^api/', include(rest_urls))
    ]

At this point you'll be able to make POST & DELETE requests to /api/pushy/device. An example request (using [httpie](https://github.com/jkbrzt/httpie) tool) to create a key is::

    http http://<URL>/api/pushy/device/ key=<key-here> type=ios --json

To delete a key::

    http delete http://<URL>/api/pushy/device/ key=<key-here> --json

Admin
-----
Django-pushy also provides an admin interface to it's models so that you can add a push notification from admin.

For that to work, you need to add "check_pending_push_notifications" task into your periodic tasks in celery admin. Make sure you setup::

    djcelery.setup_loader()
    CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'


And don't forget to run celerybeat.

Running the tests
-----------------
Install mock::

    pip install mock

then run the following from the project's root::

    py.test .


License
-------

MIT
