from setuptools import setup

setup(
    name='Django-Pushy',
    version='1.0.0',
    author='Rakan Alhneiti',
    author_email='rakan.alhneiti@gmail.com',

    # Packages
    packages=[
        'pushy',
        'pushy/contrib',
        'pushy/contrib/rest_api',
        'pushy/migrations',
    ],
    include_package_data=True,

    # Details
    url='https://github.com/rakanalh/django-pushy',

    license='LICENSE.txt',
    description='Handle push notifications at scale.',
    long_description=open('README.rst').read(),

    # Dependent packages (distributions)
    install_requires=[
        'django>=1.6',
        'django-celery==3.1.17',
        'pushjack==1.3.0'
    ],
    extras_require={
        'rest_api': ['djangorestframework>=3.0,<3.3']
    }
)
