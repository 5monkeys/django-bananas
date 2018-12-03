from collections import OrderedDict

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.http import Http404
from django.urls.exceptions import NoReverseMatch
from rest_framework import serializers, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .versioning import BananasVersioning


class BananasAPIView(viewsets.ViewSet):

    versioning_class = BananasVersioning


class NavigationAPIView(views.APIView):
    """
    The default basic root view for DefaultRouter
    """

    _ignore_model_permissions = True
    schema = None  # exclude from schema
    api_root_dict = None

    def get(self, request, *args, **kwargs):
        # Return a plain {"name": "hyperlink"} response.
        ret = OrderedDict()
        namespace = request.resolver_match.namespace
        for key, url_name in self.api_root_dict.items():
            if namespace:
                url_name = namespace + ":" + url_name
            try:
                ret[key] = {
                    "endpoint": reverse(
                        url_name,
                        args=args,
                        kwargs=kwargs,
                        request=request,
                        format=kwargs.get("format", None),
                    )
                }
            except NoReverseMatch:
                # Don't bail out if eg. no list routes exist, only detail routes.
                continue

        return Response(ret)


class AuthenticationAPIView(BananasAPIView):

    permission_classes = (IsAuthenticated,)

    # def list(self, request):
    # # """ Placeholder for api root listing """
    # # raise Http404
    # pass

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        """
        # TODO: Decorate api with sensitive post parameters as Django admin do?
        # from django.utils.decorators import method_decorator
        # from django.views.decorators.debug import sensitive_post_parameters
        # sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())
        """
        login_form = AuthenticationForm(request, data=request.data)

        if not login_form.is_valid():
            raise serializers.ValidationError(login_form.errors)

        auth_login(request, login_form.get_user())

        # TODO: Return user?
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get", "post"])
    def logout(self, request):
        auth_logout(request)
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["patch"])
    def change_password(self, request):
        password_form = PasswordChangeForm(request.user, data=request.data)

        if not password_form.is_valid():
            raise serializers.ValidationError(password_form.errors)

        password_form.save()

        return Response(status=status.HTTP_202_ACCEPTED)
