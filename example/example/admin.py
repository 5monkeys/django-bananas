from bananas.admin import AdminView, register
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from . import models


@register
class BananasAdmin(AdminView):
    verbose_name = _('Bananas')
    permissions = (('foobar_permission', 'Can foo bars'),)
    searchbar = True
    tools = (
        (_('home'), 'admin:index', 'has_access'),
        ('superadmin only', 'https://foo.bar/', 'foobar_permission'),
    )

    def get(self, request):
        context = {
            'result_count': 123 if request.GET.get('q') else 0
        }
        return self.render('bananas.html', context)


@admin.register(models.Monkey)
class MonkeyAdmin(admin.ModelAdmin):
    list_display = ('id',)
    list_filter = ('user__username',)
    raw_id_fields = ('user',)
    date_hierarchy = 'date_created'
    actions_on_top = True
    actions_on_bottom = True
    actions_selection_counter = False
