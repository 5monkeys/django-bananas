import re
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

import django
from django.apps import apps
from django.conf import settings as django_settings
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.admin.sites import site as django_admin_site
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Model
from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import render
from django.urls import URLPattern, URLResolver, re_path, reverse, reverse_lazy
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.safestring import SafeText, mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from bananas.environment import env

__all__ = ["ModelAdminView", "ViewTool", "AdminView", "register", "site"]


MT = TypeVar("MT", bound=Model)


class ExtendedAdminSite(AdminSite):
    enable_nav_sidebar = False
    default_settings: ClassVar[Dict[str, Any]] = {
        "INHERIT_REGISTERED_MODELS": env.get_bool(
            "DJANGO_ADMIN_INHERIT_REGISTERED_MODELS", True
        ),
        "SITE_TITLE": env.get("DJANGO_ADMIN_SITE_TITLE", AdminSite.site_title),
        "SITE_HEADER": env.get("DJANGO_ADMIN_SITE_HEADER", "admin"),
        "SITE_VERSION": env.get("DJANGO_ADMIN_SITE_VERSION", django.__version__),
        "INDEX_TITLE": env.get("DJANGO_ADMIN_INDEX_TITLE", AdminSite.index_title),
        "PRIMARY_COLOR": env.get("DJANGO_ADMIN_PRIMARY_COLOR", "#34A77B"),
        "SECONDARY_COLOR": env.get("DJANGO_ADMIN_SECONDARY_COLOR", "#20AA76"),
        "LOGO": env.get("DJANGO_ADMIN_LOGO", "admin/bananas/img/django.svg"),
        "LOGO_ALIGN": env.get("DJANGO_ADMIN_LOGO_ALIGN", "middle"),
        "LOGO_STYLE": env.get("DJANGO_ADMIN_LOGO_STYLE"),
    }
    settings: Dict[str, Any]

    def __init__(self, name: str = "admin") -> None:
        super().__init__(name=name)
        self.settings = dict(self.default_settings)
        self.settings.update(getattr(django_settings, "ADMIN", {}))

        self.site_title = self.settings["SITE_TITLE"]
        self.site_header = self.settings["SITE_HEADER"]
        self.index_title = self.settings["INDEX_TITLE"]

    def each_context(self, request: HttpRequest) -> Dict[str, Any]:
        context = super().each_context(request)
        context.update(settings=self.settings)
        return context

    @property
    def urls(self) -> Tuple[List[Union[URLResolver, URLPattern]], str, str]:
        if self.settings["INHERIT_REGISTERED_MODELS"]:
            for model, admin in list(django_admin_site._registry.items()):
                # django_admin_site.unregister(model)
                self._registry[model] = admin.__class__(model, self)
        return self.get_urls(), "admin", self.name


class ModelAdminView(ModelAdmin):
    @cached_property
    def access_permission(self) -> str:
        meta = self.model._meta
        codename = meta.permissions[0][0]  # First perm codename
        return f"{meta.app_label}.{codename}"

    def get_urls(self) -> List[URLPattern]:
        app_label = self.model._meta.app_label
        View: Type[AdminView] = self.model.View
        info = app_label, View.label
        urlpatterns = [
            re_path(
                r"^$",
                self.admin_view(View.as_view(admin=self)),
                name="{}_{}".format(*info),
            ),
            # We add the same url here with _changelist to make sure the
            # admin app index reverse urls to correct view.
            re_path(
                r"^$",
                self.admin_view(View.as_view(admin=self)),
                name="{}_{}_changelist".format(*info),
            ),
        ]
        extra_urls = self.model.View(admin=self).get_urls()
        if extra_urls:
            urlpatterns += extra_urls
        return urlpatterns

    def admin_view(
        self, view: Callable[..., HttpResponseBase], perm: Optional[str] = None
    ) -> Callable[..., HttpResponseBase]:
        if perm is not None:
            perm = self.get_permission(perm)
        else:
            perm = self.access_permission

        admin_login_url = reverse_lazy("admin:login")
        view = user_passes_test(
            lambda u: u.is_active and hasattr(u, "is_staff") and u.is_staff,
            login_url=admin_login_url,
        )(view)
        view = permission_required(perm, login_url=admin_login_url)(view)
        return view

    def get_permission(self, perm: str) -> str:
        if "." not in perm:
            perm = f"{self.model._meta.app_label}.{perm}"
        return perm

    def has_module_permission(self, request: HttpRequest) -> bool:
        return bool(request.user.has_perm(self.access_permission))

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[MT] = None
    ) -> bool:
        return bool(request.user.has_perm(self.access_permission))

    # TODO: Remove obj?
    def has_add_permission(
        self, request: HttpRequest, obj: Optional[MT] = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[MT] = None
    ) -> bool:
        return False

    def get_context(self, request: WSGIRequest, **extra: Any) -> Dict[str, Any]:
        opts = self.model._meta
        context = self.admin_site.each_context(request)
        context.update(
            {
                "app_label": opts.app_label,
                "model_name": force_str(opts.verbose_name_plural),
                "title": force_str(opts.verbose_name_plural),
                "cl": {"opts": opts},  # change_list.html requirement
                "opts": opts,  # change_form.html requirement
                "media": self.media,
            }
        )
        context.update(extra or {})
        return context


# Call without parenthesis: @register
@overload
def register(
    view: Type["AdminView"],
    *,
    admin_site: Optional[AdminSite] = None,
    admin_class: Type[ModelAdmin] = ModelAdminView,
) -> Type["AdminView"]: ...


# Call with parenthesis: @register()
@overload
def register(
    view: None = ...,
    *,
    admin_site: Optional[AdminSite] = None,
    admin_class: Type[ModelAdmin] = ModelAdminView,
) -> Callable[[Type["AdminView"]], Type["AdminView"]]: ...


def register(
    view: Optional[Type["AdminView"]] = None,
    *,
    admin_site: Optional[AdminSite] = None,
    admin_class: Type[ModelAdmin] = ModelAdminView,
) -> Union[Type["AdminView"], Callable[[Type["AdminView"]], Type["AdminView"]]]:
    """
    Register a generic class based view wrapped with ModelAdmin and fake model

    :param view: The AdminView to register.
    :param admin_site: The AdminSite to register the view on.
        Defaults to bananas.admin.ExtendedAdminSite.
    :param admin_class: The ModelAdmin class to use for eg. permissions.
        Defaults to bananas.admin.ModelAdminView.

    Example:

    @register  # Or with args @register(admin_class=MyModelAdminSubclass)
    class MyAdminView(bananas.admin.AdminView):
        def get(self, request):
            return self.render('template.html', {})

    # Also possible:
    register(MyAdminView, admin_class=MyModelAdminSublass)

    """
    if not admin_site:
        admin_site = site

    def wrapped(inner_view: Type["AdminView"]) -> Type["AdminView"]:
        module = inner_view.__module__
        match = re.search(r"\.?(\w+)\.admin", module)
        assert match is not None
        app_label = match.group(1)
        app_config = apps.get_app_config(app_label)

        label = getattr(inner_view, "label", None)
        if not label:
            label = re.sub("(Admin)|(View)", "", inner_view.__name__).lower()
        inner_view.label = label

        model_name = label.capitalize()
        verbose_name = getattr(inner_view, "verbose_name", model_name)
        inner_view.verbose_name = verbose_name

        access_perm_codename = "can_access_" + model_name.lower()
        access_perm_name = str(_("Can access {verbose_name}")).format(
            verbose_name=verbose_name
        )
        # The first permission here is expected to be
        # the general access permission.
        permissions = (
            (access_perm_codename, access_perm_name),
            *list(getattr(inner_view, "permissions", [])),
        )

        model = type(
            model_name,
            (Model,),
            {
                "__module__": module + ".__models__",  # Fake
                "View": inner_view,
                "app_config": app_config,
                "Meta": type(
                    "Meta",
                    (object,),
                    {
                        "managed": False,
                        "abstract": True,
                        "app_label": app_config.label,
                        "verbose_name": verbose_name,
                        "verbose_name_plural": verbose_name,
                        "permissions": permissions,
                    },
                ),
            },
        )

        assert admin_site is not None
        admin_site._registry[model] = admin_class(model, admin_site)
        return inner_view

    if view is None:  # Used as a decorator
        return wrapped

    return wrapped(view)


class ViewTool:
    def __init__(
        self, text: str, link: str, perm: Optional[str] = None, **attrs: Any
    ) -> None:
        self.text = text
        self._link = link
        self.perm = perm

        html_class = attrs.pop("html_class", None)
        if html_class is not None:
            attrs.setdefault("class", html_class)
        self._attrs = attrs

    @property
    def attrs(self) -> SafeText:
        return mark_safe(" ".join(f"{k}={v}" for k, v in self._attrs.items()))

    @property
    def link(self) -> str:
        if "/" not in self._link:
            return reverse(self._link)
        return self._link


class AdminView(View):
    tools: ClassVar[
        Optional[List[Union[Tuple[str, str], Tuple[str, str, str], ViewTool]]]
    ] = None
    action: ClassVar[Optional[str]] = None
    admin: ClassVar[Optional[ModelAdminView]] = None

    label: str
    verbose_name: str
    request: WSGIRequest

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        # Try to fetch set action first.
        # This should be the view name for custom views
        action = self.action
        if action is None:
            return super().dispatch(request, *args, **kwargs)

        handler: Callable[..., HttpResponseBase] = getattr(self, action)
        return handler(request, *args, **kwargs)

    def get_urls(self) -> List[URLPattern]:
        """Should return a list of urls
        Views should be wrapped in `self.admin_view` if the view isn't
        supposed to be accessible for non admin users.
        Omitting this can cause threading issues.

        Example:

            return [
                url(r'^custom/$',
                    self.admin_view(self.custom_view))
            ]
        """
        return []

    def get_tools(
        self,
    ) -> Optional[List[Union[Tuple[str, str], Tuple[str, str, str], ViewTool]]]:
        # Override point, self.request is available.
        return self.tools

    def get_view_tools(self) -> List[ViewTool]:
        tools = []
        all_tools = self.get_tools()
        if all_tools:
            for tool in all_tools:
                if isinstance(tool, (list, tuple)):
                    perm = None
                    # Mypy doesn't change type on a len(...) call
                    # See: https://github.com/python/mypy/issues/1178
                    if len(tool) == 3:
                        tool, perm = tool[:-1], tool[-1]
                    text, link = tool
                    tool = ViewTool(text, link, perm=perm)
                else:
                    # Assume ViewTool
                    perm = tool.perm
                if perm and not self.has_permission(perm):
                    continue

                tools.append(tool)

        return tools

    def admin_view(
        self,
        view: Callable[..., HttpResponseBase],
        perm: Optional[str] = None,
        **initkwargs: Any,
    ) -> Callable[..., HttpResponseBase]:
        assert self.admin is not None
        view = self.__class__.as_view(
            action=view.__name__, admin=self.admin, **initkwargs
        )
        return self.admin.admin_view(view, perm=perm)

    def get_permission(self, perm: str) -> str:
        assert self.admin is not None
        return self.admin.get_permission(perm)

    def has_permission(self, perm: str) -> bool:
        perm = self.get_permission(perm)
        return bool(self.request.user.has_perm(perm))

    def has_access(self) -> bool:
        assert self.admin is not None
        return self.has_permission(self.admin.access_permission)

    def get_context(self, **extra: Any) -> Dict[str, Any]:
        assert self.admin is not None
        return self.admin.get_context(
            self.request, view_tools=self.get_view_tools(), **extra
        )

    def render(
        self, template: str, context: Optional[Dict[str, Any]] = None
    ) -> HttpResponse:
        extra = context or {}
        return render(self.request, template, self.get_context(**extra))


site = ExtendedAdminSite()
