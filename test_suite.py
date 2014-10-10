import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

import django
if django.get_version().startswith('1.7'):
    django.setup()

from django.core import management
management.call_command('test', 'tests')
