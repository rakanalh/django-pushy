# assert warnings are enabled
import warnings

warnings.simplefilter('ignore', Warning)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'pushy',
]

MIDDLEWARE_CLASSES = []

SECRET_KEY = 'django-pushy-key'
SITE_ID = 1
ROOT_URLCONF = 'core.urls'

CELERY_ALWAYS_EAGER = True
PUSHY_GCM_API_KEY = 'blah-blah'

PUSHY_GCM_JSON_PAYLOAD = False

PUSHY_APNS_CERTIFICATE_FILE = 'aps_development.pem'
PUSHY_APNS_KEY_FILE = 'private_key.pem'