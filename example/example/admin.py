from bananas.admin import AdminView, register
from django.utils.translation import gettext_lazy as _


@register
class BananasAdmin(AdminView):
    verbose_name = _('Bananas')
    tools = (
        (_('home'), 'admin:index', 'has_access'),
        ('superadmin only', 'https://foo.bar/', 'foobar_permission'),
    )

    def get(self, request):
        return self.render('bananas.html')
