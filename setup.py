#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='django-bananas',
    description='Django Bananas - Django extensions the monkey way',
    version=__import__('bananas').__version__,
    packages=find_packages(exclude=['_*']),
    install_requires=[],
)
