from django.conf.urls import url
from django.contrib import admin
from .models import Simple

admin.site.register(Simple)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]
