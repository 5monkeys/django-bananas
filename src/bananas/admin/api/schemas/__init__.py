from drf_yasg.utils import (
    swagger_auto_schema as schema,
    swagger_serializer_method as schema_serializer_method,
)

from .yasg import (
    BananasSimpleRouter as BananasRouter,
    BananasSwaggerSchema as BananasSchema,
)

__all__ = (
    "schema",
    "schema_serializer_method",
    "BananasRouter",
    "BananasSchema",
)
