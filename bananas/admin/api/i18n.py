from django.views.i18n import JavaScriptCatalog


class RawTranslationCatalog(JavaScriptCatalog):
    def render_to_response(self, context, **response_kwargs):
        return context
