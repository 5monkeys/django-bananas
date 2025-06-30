import base64
import binascii
import math
import os
import uuid
from itertools import chain
from typing import Any, ClassVar, Dict, Final, Mapping, Optional, Sized

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Missing: ...


MISSING: Final = Missing()


class ModelDict(Dict[str, Any]):
    _nested: Optional[Dict[str, "ModelDict"]] = None

    def __getattr__(self, item: str) -> Any:
        """
        Try to to get attribute as key item.
        Fallback on prefixed nested keys.
        Finally fallback on real attribute lookup.
        """
        try:
            return self.__getitem__(item)
        except KeyError:
            try:
                return self.__getnested__(item)
            except KeyError:
                return self.__getattribute__(item)

    def __getnested__(self, item: str) -> "ModelDict":
        """
        Find existing items prefixed with given item
        and return a new ModelDict containing matched keys,
        stripped from prefix.

        :param str item: Item prefix key to find
        :return ModelDict:
        """
        # Ensure _nested cache
        if self._nested is None:
            self._nested: Dict[str, ModelDict] = {}

        # Try to get previously accessed/cached nested item
        value = self._nested.get(item, MISSING)

        if not isinstance(value, Missing):
            # Return previously accessed nested item
            return value

        else:
            # Find any keys matching nested prefix
            prefix = item + "__"
            keys = [key for key in self.keys() if key.startswith(prefix)]

            if keys:
                # Construct nested dict of matched keys, stripped from prefix
                n = ModelDict({key[len(item) + 2 :]: self[key] for key in keys})

                # Cache and return
                self._nested[item] = n
                return n

        # Item not a nested key, raise
        raise KeyError(item)

    def expand(self) -> "ModelDict":
        keys = list(self)
        for key in keys:
            field, __, nested_key = key.partition("__")
            if nested_key:
                if field not in keys:
                    nested = self.__getnested__(field)
                    if isinstance(nested, self.__class__):
                        nested = nested.expand()
                    self[field] = nested
                del self[key]
        return ModelDict(self)

    @classmethod
    # Ignore types until no longer work-in-progress.
    def from_model(cls, model, *fields, **named_fields):  # type: ignore[no-untyped-def]
        """
        Work-in-progress constructor,
        consuming fields and values from django model instance.
        """
        d = ModelDict()

        if not (fields or named_fields):
            # Default to all fields
            fields = [  # type: ignore[assignment]
                f.attname for f in model._meta.concrete_fields
            ]

        not_found = object()

        for name, field in chain(zip(fields, fields), named_fields.items()):
            _fields = field.split("__")
            value = model
            for i, _field in enumerate(_fields, start=1):
                # NOTE: we don't want to rely on hasattr here
                previous_value = value
                value = getattr(previous_value, _field, not_found)

                if value is not_found:
                    if _field in dir(previous_value):
                        raise ValueError(
                            "{!r}.{} had an AttributeError exception".format(
                                previous_value, _field
                            )
                        )
                    else:
                        raise AttributeError(
                            f"{previous_value!r} does not have {_field!r} attribute"
                        )

                elif value is None:
                    if name not in named_fields:
                        name = "__".join(_fields[:i])
                    break

            d[name] = value

        return d


class TimeStampedModel(models.Model):
    """
    Provides automatic date_created and date_modified fields.
    """

    date_created = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        auto_now_add=True,
        verbose_name=_("date created"),
    )
    date_modified = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        auto_now=True,
        verbose_name=_("date modified"),
    )

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        if "update_fields" in kwargs and "date_modified" not in kwargs["update_fields"]:
            update_fields = list(kwargs["update_fields"])
            update_fields.append("date_modified")
            kwargs["update_fields"] = update_fields
        super().save(*args, **kwargs)


class UUIDModel(models.Model):
    """
    Provides auto-generating UUIDField as the primary key for a model.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    class Meta:
        abstract = True


class SecretField(models.CharField):
    description = _("Generates and stores a random key.")

    default_error_messages = {  # noqa: RUF012
        "random-is-none": _("%(cls)s.get_random_bytes returned None"),
        "random-too-short": _(
            "Too few random bytes received from "
            "get_random_bytes. Number of"
            " bytes=%(num_bytes)s,"
            " min_length=%(min_length)s"
        ),
    }

    def __init__(
        self,
        verbose_name: Optional[str] = None,
        num_bytes: int = 32,
        min_bytes: int = 32,
        auto: bool = True,
        **kwargs: Any,
    ):
        self.num_bytes, self.auto, self.min_length = num_bytes, auto, min_bytes

        field_length = self.get_field_length(self.num_bytes)

        defaults: Mapping[str, Any] = {
            "max_length": field_length,
            **kwargs,
            **(
                {
                    "editable": False,
                    "blank": True,
                }
                if self.auto
                else {}
            ),
        }

        super().__init__(verbose_name, **defaults)

    @staticmethod
    def get_field_length(num_bytes: int) -> int:
        """
        Return the length of hexadecimal byte representation of ``n`` bytes.

        :param num_bytes:
        :return: The field length required to store the byte representation.
        """
        return num_bytes * 2

    def pre_save(self, model_instance: models.Model, add: bool) -> Any:
        if self.auto and add:
            value = self.get_random_str()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super().pre_save(model_instance, add)

    def get_random_str(self) -> str:
        random = self.get_random_bytes()
        self._check_random_bytes(random)
        return binascii.hexlify(random).decode("utf8")

    def _check_random_bytes(self, random: Optional[Sized]) -> None:
        if random is None:
            raise ValidationError(
                self.error_messages["random-is-none"],
                code="invalid",
                params={"cls": self.__class__.__name__},
            )

        if len(random) < self.min_length:
            raise ValidationError(
                self.error_messages["random-too-short"],
                code="invalid",
                params={"num_bytes": len(random), "min_length": self.min_length},
            )

    def get_random_bytes(self) -> bytes:
        return os.urandom(self.num_bytes)


class URLSecretField(SecretField):
    @staticmethod
    def get_field_length(num_bytes: int) -> int:
        """
        Get the maximum possible length of a base64 encoded bytearray of
        length ``length``.

        :param num_bytes: The length of the bytearray
        :return: The worst case length of the base64 result.
        """
        return math.ceil(num_bytes / 3.0) * 4

    @staticmethod
    def y64_encode(s: bytes) -> bytes:
        """
        Implementation of Y64 non-standard URL-safe base64 variant.

        See http://en.wikipedia.org/wiki/Base64#Variants_summary_table

        :return: base64-encoded result with substituted
        ``{"+", "/", "="} => {".", "_", "-"}``.
        """
        first_pass = base64.urlsafe_b64encode(s)
        return first_pass.translate(bytes.maketrans(b"+/=", b"._-"))

    def get_random_str(self) -> str:
        random = self.get_random_bytes()
        self._check_random_bytes(random)
        return self.y64_encode(random).decode("utf-8")
