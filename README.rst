django-pushy
============
Your push notifications handled at scale.

What does it do?
----------------
Python / Django app that provides push notifications functionality with celery. The main purpose of this app is to help you send push notifications to your users at scale. If you have lots of registered device keys, django-pushy will split your keys into smaller groups which run in parallel making the process of sending notifications faster.

Setup
-----
You can install the library directly from pypi using pip::

	$ pip install django-push-notifications


Add django-pushy to your INSTALLED_APPS::

	INSTALLED_APPS = (
		...
		"djcelery",
		"push_notifications"
	)

Configurations::

	PUSHY_QUEUE_DEFAULT_NAME = 'default'
	PUSHY_DEVICE_KEY_LIMIT = 1000

Then perform "python manage.py syncdb" to install the app's DB tables.

How do i use it?
----------------

Whenever you need to push a notification, use the following code::

    from pushy import send_push_notification
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

