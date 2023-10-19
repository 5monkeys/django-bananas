from typing import Any, Dict

from django.views.i18n import JavaScriptCatalog


class RawTranslationCatalog(JavaScriptCatalog):
    domain = "django"

    def render_to_response(self, context: Dict[str, Any], **response_kwargs: Any) -> Dict[str, Any]:  # type: ignore[override]
        return context
