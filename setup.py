from setuptools import setup

setup(
    name='django-joblog',
    version='0.0.1',
    description='A generic django-utility that helps to log stuff to the database.',
    long_description=open("./README.md").read(),
    long_description_content_type="text/markdown",
    url='https://github.com/defgsus/django-joblog',
    author='Stefan Berke',
    author_email='s.berke@netzkolchose.de',
    license='MIT',
    packages=[
        'django_joblog',
        'django_joblog.migrations',
    ],
    zip_safe=False,
)