#!/usr/bin/env python
from os import path
from setuptools import setup, find_packages

here = path.dirname(path.abspath(__file__))

# Get the long description from the relevant file
long_description = None

try:
    with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
except Exception:
    pass


setup(
    name='django-bananas',
    description='Django Bananas - Django extensions the monkey way',
    long_description=long_description,
    url='https://github.com/5monkeys/django-bananas',
    version=__import__('bananas').__version__,
    packages=find_packages(exclude=['tests', '_*', 'example']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    tests_require=['detox', 'coverage'],
    test_suite='runtests.main'
)
