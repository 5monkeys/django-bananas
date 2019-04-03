from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    help = "Create admin permissions"

    def handle(self, *args, **options):
        if args:  # pragma: no cover
            raise CommandError("Command doesn't accept any arguments")
        return self.handle_noargs(**options)

    def handle_noargs(self, *args, **options):
        from bananas import admin
        from django.contrib import admin as django_admin
        from django.contrib.contenttypes.models import ContentType

        django_admin.autodiscover()

        for model, _ in admin.site._registry.items():
            if issubclass(getattr(model, "View", object), admin.AdminView):
                meta = model._meta

                ct, created = ContentType.objects.get_or_create(
                    app_label=meta.app_label, model=meta.object_name.lower()
                )

                if created:
                    print("Found new admin view: {} [{}]".format(ct.name, ct.app_label))

                for codename, name in model._meta.permissions:
                    p, created = Permission.objects.update_or_create(
                        codename=codename, content_type=ct, defaults=dict(name=name)
                    )
                    if created:
                        print("Created permission: {}".format(name))
