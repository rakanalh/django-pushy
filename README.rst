django-pushy
============
Your push notifications handled at scale.

.. image:: https://travis-ci.org/rakanalh/django-pushy.svg?branch=master
    :target: https://travis-ci.org/rakanalh/django-pushy
.. image:: https://pypip.in/d/django-pushy/badge.png
    :target: https://crate.io/packages/django-pushy/
    :alt: Number of PyPI downloads

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

	PUSHY_QUEUE_DEFAULT_NAME = 'default'
	PUSHY_DEVICE_KEY_LIMIT = 1000


If you're using Django < 1.7 and using south, make sure you do the following::

    pip install South==1.0
    python manage.py syncdb
    python manage.py migrate

If you're using Django 1.7, you only have to perform::

    python manage.py migrate

How do i use it?
----------------

Whenever you need to push a notification, use the following code::

    from pushy.utils import send_push_notification
    send_push_notification('YOUR TITLE', 'YOUR BODY')

and pushy will handle the rest.

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

    python tests/run_tests.py



TODO
----
1. APNS (Apple) dispatcher is still not implemented
2. Allow Device queryset to be filtered in case not all devices were targeted
3. Additional push notification data to be included with payload