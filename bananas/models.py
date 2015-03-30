from django.db import models
from django.utils.translation import ugettext_lazy as _


class TimeStampedModel(models.Model):

    date_created = models.DateTimeField(blank=True, null=True, editable=False,
                                        auto_now_add=True,
                                        verbose_name=_('date created'))
    date_modified = models.DateTimeField(blank=True, null=True, editable=False,
                                         auto_now=True,
                                         verbose_name=_('date modified'))

    class Meta:
        abstract = True
