from drf_yasg.utils import (  # noqa
    swagger_auto_schema as schema,
    swagger_serializer_method as schema_serializer_method,
)

from .yasg import (  # noqa
    BananasSimpleRouter as BananasRouter,
    BananasSwaggerSchema as BananasSchema,
)
