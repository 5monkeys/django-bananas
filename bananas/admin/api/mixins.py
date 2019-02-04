from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.reverse import reverse
from rest_framework.utils import formatting

from bananas.models import ModelDict

from .schemas import BananasSchema
from .versioning import BananasVersioning

UNDEFINED = object()


class BananasAPI(object):

    versioning_class = BananasVersioning
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAdminUser,)
    swagger_schema = BananasSchema  # for DRF: schema = BananasSchema()

    @classmethod
    def get_admin_meta(cls):
        meta = getattr(cls, "_admin_meta", None)

        if meta is None:
            # TODO: Get proper app_label, not only root package
            app_label, __, __ = cls.__module__.lower().partition(".")
            name = cls.get_view_name(cls)

            basename = getattr(cls, "basename", None)
            if basename is None:
                if type(name).__name__ == "__proxy__":
                    # name is lazy, probably gettext, extract basename from class name
                    basename = cls.get_view_name(cls, respect_name=False)
                else:
                    basename = name
                basename = basename.replace(" ", "_").lower()

            meta = ModelDict(
                app_label=app_label,
                basename=basename,
                name=name,
                exclude_tags=[],
                verbose_name=None,
                verbose_name_plural=name,
            )

            admin = getattr(cls, "Admin", None)
            if admin is not None:
                meta.update(
                    {
                        key: getattr(admin, key)
                        for key in filter(
                            lambda key: key in meta, admin.__dict__.keys()
                        )
                    }
                )

            basename = "{}.{}".format(meta.app_label, meta.basename)
            meta.update(
                dict(
                    basename=basename,
                )
            )
            cls._admin_meta = meta

        return meta

    def reverse_action(self, url_name, *args, **kwargs):
        """
        Extended DRF with fallback to requested namespace if request.version is missing
        """
        if self.request and not self.request.version:
            return reverse(self.get_url_name(url_name), *args, **kwargs)

        return super().reverse_action(url_name, *args, **kwargs)

    def get_url_name(self, action_url_name="list"):
        """
        Get full namespaced url name to use for reverse()
        """
        url_name = "{}-{}".format(self.basename, action_url_name)

        namespace = self.request.resolver_match.namespace
        if namespace:
            url_name = "{}:{}".format(namespace, url_name)

        return url_name

    def get_view_name(self, respect_name=True):
        """
        Get or generate human readable view name.
        Extended version from DRF to support usage from both class and instance.
        """
        if isinstance(self, type):
            view = self
        else:
            view = self.__class__

        # Name may be set by some Views, such as a ViewSet.
        if respect_name:
            name = getattr(view, "name", None)
            if name is not None:
                return name

        name = view.__name__
        for suffix in ("ViewSet", "View", "API", "Admin"):
            name = formatting.remove_trailing_string(name, suffix)
        name = formatting.camelcase_to_spaces(name)

        # Suffix may be set by some Views, such as a ViewSet.
        suffix = getattr(view, "suffix", None)
        if suffix:
            name += " " + suffix

        return name


class SchemaSerializerMixin(object):

    def get_serializer_class(self, status_code: int = None):
        serializer_class = super().get_serializer_class()

        action = getattr(self, self.action, None)
        schema = getattr(action, "_swagger_auto_schema", None)
        if schema:
            responses = schema.get("responses")
            if responses:
                status_code = sorted(responses.keys())[0]
                if status_code < 300:
                    serializer_class = responses[status_code]

        return serializer_class
