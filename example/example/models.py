from django.conf import settings
from django.db import models

from bananas.models import TimeStampedModel


class Monkey(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return 'https://www.5monkeys.se/'
