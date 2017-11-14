# coding=utf-8
import re
from django.apps import apps
from django.db.models import Model
from django.conf import settings as django_settings
from django.conf.urls import url
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.admin.sites import site as django_admin_site
from django.contrib.auth.decorators import (
    user_passes_test,
    permission_required,
    login_required,
)
from django.shortcuts import render
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from .environment import env
from . import compat


class ExtendedAdminSite(AdminSite):

    default_settings = {
        'INHERIT_REGISTERED_MODELS': env.get_bool(
            'DJANGO_ADMIN_INHERIT_REGISTERED_MODELS', True),
        'SITE_TITLE': env.get(
            'DJANGO_ADMIN_SITE_TITLE', AdminSite.site_title),
        'SITE_HEADER': env.get(
            'DJANGO_ADMIN_SITE_HEADER', 'admin'),
        'INDEX_TITLE': env.get(
            'DJANGO_ADMIN_INDEX_TITLE', AdminSite.index_title),
        'PRIMARY_COLOR': env.get(
            'DJANGO_ADMIN_PRIMARY_COLOR', '#34A77B'),
        'SECONDARY_COLOR': env.get(
            'DJANGO_ADMIN_SECONDARY_COLOR', '#20AA76'),
        'LOGO': env.get(
            'DJANGO_ADMIN_LOGO', 'admin/bananas/img/django.svg'),
        'LOGO_ALIGN': env.get(
            'DJANGO_ADMIN_LOGO_ALIGN', 'middle'),
    }

    def __init__(self, name='admin'):
        super().__init__(name=name)
        self.settings = dict(self.default_settings)
        self.settings.update(getattr(django_settings, 'ADMIN', {}))

        self.site_title = self.settings['SITE_TITLE']
        self.site_header = self.settings['SITE_HEADER']
        self.index_title = self.settings['INDEX_TITLE']

    def each_context(self, request):
        context = super().each_context(request)
        context.update(settings=self.settings)
        return context

    @property
    def urls(self):
        if self.settings['INHERIT_REGISTERED_MODELS']:
            for model, admin in list(django_admin_site._registry.items()):
                # django_admin_site.unregister(model)
                self._registry[model] = admin.__class__(model, self)
        return self.get_urls(), 'admin', self.name


class ModelAdminView(ModelAdmin):

    def __init__(self, *args, **kwargs):
        super(ModelAdminView, self).__init__(*args, **kwargs)

    def get_urls(self):
        app_label = self.model._meta.app_label

        self.access_permission = '{app_label}.{codename}'.format(
            app_label=app_label,
            codename=self.model._meta.permissions[0][0]  # First perm codename
        )

        View = self.model.View
        view = View.as_view(admin=self)
        view = user_passes_test(lambda u: u.is_active and u.is_staff)(view)
        view = permission_required(self.access_permission)(view)
        view = login_required(view)

        info = app_label, View.label

        urlpatterns = compat.urlpatterns(
            url(r'^$', view, name='{}_{}'.format(*info)),
            url(r'^$', view, name='{}_{}_changelist'.format(*info)),
        )

        extra_urls = self.model.View(admin=self).get_urls()
        if extra_urls:
            urlpatterns += extra_urls

        return urlpatterns

    def has_module_permission(self, request):
        return request.user.has_perm(self.access_permission)

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm(self.access_permission)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_context(self, request, **extra):
        opts = self.model._meta
        context = self.admin_site.each_context(request)
        context.update({
            'app_label': opts.app_label,
            'model_name': force_text(opts.verbose_name_plural),
            'title': force_text(opts.verbose_name_plural),
            'cl': {'opts': opts},  # change_list.html requirement
            'media': self.media,
        })
        context.update(extra or {})
        return context


def register(view, admin_site=None):
    """
    Register a generic class based view wrapped with ModelAdmin and fake model
    """
    app_package = view.__module__[:view.__module__.index('.admin')]
    app_config = apps.get_app_config(app_package)

    label = getattr(view, 'label', None)
    if not label:
        label = re.sub('(Admin)|(View)', '', view.__name__).lower()
    view.label = label

    model_name = label.capitalize()
    verbose_name = getattr(view, 'verbose_name', model_name)
    view.verbose_name = verbose_name

    access_perm_codename = 'can_access_' + model_name.lower()
    access_perm_name = _('Can access {verbose_name}').format(
        verbose_name=verbose_name
    )
    permissions = tuple([
        (access_perm_codename, access_perm_name)
    ] + list(getattr(view, 'permissions', [])))

    model = type(model_name, (Model,), {
        '__module__': view.__module__ + '.__models__',  # Fake
        'View': view,
        'app_config': app_config,
        'Meta': type('Meta', (object,), dict(
            managed=False,
            abstract=True,
            app_label=app_config.label,
            verbose_name=verbose_name,
            verbose_name_plural=verbose_name,
            permissions=permissions,
        ))
    })

    # Do register on admin site
    if not admin_site:
        admin_site = site

    admin_site._registry[model] = ModelAdminView(model, admin_site)


class AdminView(View):

    admin = None
    tools = None

    def get_urls(self):
        return None

    def get_view_tools(self):
        tools = []

        if self.tools:
            for tool in self.tools:
                perm = None
                if len(tool) == 3:
                    tool, perm = tool[:-1], tool[-1]
                if perm and not self.has_permission(perm):
                    continue
                text, link = tool
                if '/' not in link:
                    link = compat.reverse(link)
                tools.append((text, link))

        return tools

    def admin_view(self, view, perm=None):
        perm = perm or 'can_access_' + self.admin.model._meta.verbose_name
        perm = self.get_permission(perm)
        return permission_required(perm)(view)

    def get_permission(self, perm):
        if '.' not in perm:
            perm = '{}.{}'.format(self.admin.model._meta.app_label, perm)
        return perm

    def has_permission(self, perm):
        perm = self.get_permission(perm)
        return self.request.user.has_perm(perm)

    def has_access(self):
        perm = 'can_access_' + self.admin.model._meta.verbose_name
        return self.has_permission(perm)

    def get_context(self, **extra):
        return self.admin.get_context(
            self.request,
            view_tools=self.get_view_tools(),
            **extra
        )

    def render(self, template, context=None):
        extra = context or {}
        return render(
            self.request,
            template,
            self.get_context(**extra)
        )


site = ExtendedAdminSite()
