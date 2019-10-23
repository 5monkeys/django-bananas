from rest_framework import VERSION

version = tuple(map(int, VERSION.split(".")))

if version[:2] >= (3, 10):
    from rest_framework.schemas.coreapi import is_custom_action
else:
    from rest_framework.schemas.generators import is_custom_action
