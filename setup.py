from setuptools import setup

setup(
    name='Django-Pushy',
    version='0.1.0',
    author='Rakan Alhneiti',
    author_email='rakan.alhneiti@gmail.com',

    # Packages
    packages=['pushy'],
    include_package_data=True,

    # Details
    url='https://github.com/rakanalh/django-pushy',

    license='LICENSE.txt',
    description='Handle push notifications at scale.',
    long_description=open('README.rst').read(),

    # Dependent packages (distributions)
    install_requires=[
        'python-gcm',
        'django',
        'django-celery'
    ],
)