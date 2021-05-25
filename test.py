from rest_framework import mixins
from bananas.admin.api.views import BananasAdminAPI

class Subclass(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    BananasAdminAPI,
): ...
