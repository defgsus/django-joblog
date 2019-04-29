from setuptools import setup


long_description = "%s\n\n## Changelog\n%s" % (
    open("./README.md").read(),
    open("./HISTORY.md").read(),
)


setup(
    name='django-joblog',
    version='0.2.3',
    description='A generic django-utility that helps to log stuff to the database.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/defgsus/django-joblog',
    author='Stefan Berke',
    author_email='s.berke@netzkolchose.de',
    license='MIT',
    packages=[
        'django_joblog',
        'django_joblog.migrations',
        'django_joblog.management',
        'django_joblog.management.commands',
        'django_joblog.tests',
        'django_joblog.impl',
    ],
    zip_safe=False,
    install_requires=['django>=1.10.0'],
    python_requires='>=2.6, <4',
    keywords="django database logging",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
