from django.conf import settings


def pytest_configure():
    settings.configure(
        ROOT_URLCONF='tests.urls',

        ALLOWED_HOSTS=['testserver'],

        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test_db'
            }
        },

        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',

            'rest_framework',
            'pushy',
            'tests'
        ],

        PUSHY_GCM_API_KEY='SOME_TEST_KEY',
        PUSHY_GCM_JSON_PAYLOAD=False,
        PUSHY_APNS_CERTIFICATE_FILE='/var/apns/certificate',
        PUSHY_APNS_SANDBOX=False
    )
