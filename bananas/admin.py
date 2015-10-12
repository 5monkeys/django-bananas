from django.conf import settings as django_settings
from django.contrib.admin import AdminSite
from django.contrib.admin.sites import site as django_admin_site


class ExtendedAdminSite(AdminSite):

    default_settings = {
        'INHERIT_REGISTERED_MODELS': True,
        'SITE_TITLE': AdminSite.site_title,
        'SITE_HEADER': AdminSite.site_header,
        'INDEX_TITLE': AdminSite.index_title,
        'BACKGROUND_COLOR': '#444'
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


site = ExtendedAdminSite()
