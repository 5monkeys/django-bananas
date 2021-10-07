from django.urls import re_path

from bananas import admin


@admin.register()
class SimpleAdminView(admin.AdminView):
    permissions = [
        ("can_do_special_stuff", "Can do special stuff"),
    ]
    tools = [
        ("Special Action", "admin:tests_simple_special", "can_do_special_stuff"),
        admin.ViewTool(
            "Even more special action",
            "https://example.org",
            html_class="addlink",
        ),
    ]

    def get_urls(self):
        return [
            re_path(
                r"^custom/$",
                self.admin_view(self.custom_view),
                name="tests_simple_custom",
            ),
            re_path(
                r"^special/$",
                self.admin_view(
                    self.special_permission_view, perm="can_do_special_stuff"
                ),
                name="tests_simple_special",
            ),
        ]

    def get(self, request):
        return self.render("simple.html", {"context": "get"})

    def custom_view(self, request):
        assert self.has_access()  # For coverage...
        return self.render("simple.html", {"context": "custom"})

    def special_permission_view(self, request):
        return self.render("simple.html", {"context": "special"})
