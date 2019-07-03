"""example URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url

from bananas import admin
from bananas.admin import api

from .api import AppleViewSet, BananaViewSet, PeachViewSet, PearViewSet, UserViewSet

api.register(AppleViewSet)
api.register(BananaViewSet)
api.register(PeachViewSet)
api.register(PearViewSet)
api.register(UserViewSet)

urlpatterns = [
    url(r'^api/', include('bananas.admin.api.urls')),
    url(r'^', admin.site.urls),
]
