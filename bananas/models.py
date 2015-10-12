import math
import base64
import os
import uuid
import binascii

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


class TimeStampedModel(models.Model):
    """
    Provides automatic date_created and date_modified fields.
    """
    date_created = models.DateTimeField(blank=True, null=True, editable=False,
                                        auto_now_add=True,
                                        verbose_name=_('date created'))
    date_modified = models.DateTimeField(blank=True, null=True, editable=False,
                                         auto_now=True,
                                         verbose_name=_('date modified'))

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Provides auto-generating UUIDField as the primary key for a model.
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    class Meta:
        abstract = True


class SecretField(models.CharField):
    description = _('Generates and stores a random key.')

    default_error_messages = {
        'random-is-none': _('%(cls)s.get_random_bytes returned None'),
        'random-too-short': _('Too few random bytes received from '
                              'get_random_bytes. Number of'
                              ' bytes=%(num_bytes)s,'
                              ' min_length=%(min_length)s')
    }

    def __init__(self, verbose_name=None, num_bytes=32, min_bytes=32, auto=True,
                 **kwargs):
        self.num_bytes, self.auto, self.min_length = num_bytes, auto, min_bytes

        field_length = self.get_field_length(self.num_bytes)

        defaults = {
            'max_length': field_length,
        }
        defaults.update(kwargs)

        if self.auto:
            defaults['editable'] = False
            defaults['blank'] = True

        super(SecretField, self).__init__(verbose_name, **defaults)

    @staticmethod
    def get_field_length(num_bytes):
        """
        Return the length of hexadecimal byte representation of ``n`` bytes.

        :param num_bytes:
        :return: The field length required to store the byte representation.
        """
        return num_bytes * 2

    def pre_save(self, model_instance, add):
        if self.auto and add:
            value = self.get_random_str()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(SecretField, self).pre_save(model_instance, add)

    def get_random_str(self):
        random = self.get_random_bytes()
        self._check_random_bytes(random)
        return binascii.hexlify(random).decode('utf8')

    def _check_random_bytes(self, random):
        if random is None:
            raise ValidationError(self.error_messages['random-is-none'],
                                  code='invalid',
                                  params={'cls': self.__class__.__name__})

        if len(random) < self.min_length:
            raise ValidationError(self.error_messages['random-too-short'],
                                  code='invalid',
                                  params={'num_bytes': len(random),
                                          'min_length': self.min_length})

    def get_random_bytes(self):
        return os.urandom(self.num_bytes)


class URLSecretField(SecretField):
    @staticmethod
    def get_field_length(num_bytes):
        """
        Get the maximum possible length of a base64 encoded bytearray of
        length ``length``.

        :param num_bytes: The length of the bytearray
        :return: The worst case length of the base64 result.
        """
        return math.ceil(num_bytes / 3.0) * 4

    @staticmethod
    def y64_encode(s):
        """
        Implementation of Y64 non-standard URL-safe base64 variant.

        See http://en.wikipedia.org/wiki/Base64#Variants_summary_table

        :return: base64-encoded result with substituted
        ``{"+", "/", "="} => {".", "_", "-"}``.
        """
        first_pass = base64.urlsafe_b64encode(s)
        return first_pass.translate(bytes.maketrans(b'+/=',
                                                    b'._-'))

    def get_random_str(self):
        random = self.get_random_bytes()
        self._check_random_bytes(random)
        return self.y64_encode(random).decode('utf-8')
