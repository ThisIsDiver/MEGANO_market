from rest_framework.parsers import JSONParser

"""
Парсер текста, так как временами frontend отправляет текстом
"""
class TextPlainJSONParser(JSONParser):
    media_type = "text/plain"

    def parse(self, stream, media_type=None, parser_context=None):
        return super().parse(
            stream, media_type="application/json", parser_context=parser_context
        )
