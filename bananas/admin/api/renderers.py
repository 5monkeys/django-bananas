from django.urls.exceptions import NoReverseMatch
from rest_framework import renderers
from rest_framework.compat import urlparse

from .versioning import BananasVersioning


class NamespacedJSONOpenAPIRenderer(renderers.JSONOpenAPIRenderer):
    def get_operation(self, link, name, tag):
        operation = super().get_operation(link, name, tag)

        view = link._view  # FYI: Set in BananasSchema.get_link
        meta = view.get_admin_meta()

        operation["summary"] = str(meta.name)
        operation["operationId"] = meta.basename + ":" + name
        operation["tags"] = ["app:{}".format(meta.app_label)]

        if name == "list" or not hasattr(view, "list"):
            try:
                view.reverse_action("list")
                operation["tags"] += ["navigation"]
            except NoReverseMatch:
                pass

        return operation

    def get_structure(self, data):
        structure = super().get_structure(data)
        structure["info"]["version"] = BananasVersioning.default_version
        return structure

    def get_paths(self, document):
        """
        Temporary fix to support namespace versioning.

        See: https://github.com/calvin620707/DRF-OpenApiRender-NestUrlPatterns/blob/master/demo/demo/urls.py

        # TODO: Remove when bug fixed in DRF
        """
        paths = {}

        tag = None
        for name, link in document.links.items():
            path = urlparse.urlparse(link.url).path
            method = link.action.lower()
            paths.setdefault(path, {})
            paths[path][method] = self.get_operation(link, name, tag=tag)

        for tag, section in document.data.items():
            if not section.links:
                sub_paths = self.get_paths(section)
                paths.update(sub_paths)
                continue

            for name, link in section.links.items():
                path = urlparse.urlparse(link.url).path
                method = link.action.lower()
                paths.setdefault(path, {})
                paths[path][method] = self.get_operation(link, name, tag=tag)

        return paths
