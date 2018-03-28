from django.conf.urls import url

from bananas import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]
