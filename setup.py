#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='django-bananas',
    description='Django Bananas - Django extensions the monkey way',
    version=__import__('bananas').__version__,
    packages=find_packages(exclude=['tests', '_*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    test_suite='runtests.main'
)
