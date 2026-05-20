from django.conf import settings
from django.http import HttpResponse


class SimpleCORSMiddleware:
    """
    Minimal CORS middleware without external dependencies.
    Configure allowed origins in settings.CORS_ALLOWED_ORIGINS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        self._apply_cors_headers(request, response)
        return response

    def _apply_cors_headers(self, request, response):
        allowed_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        origin = request.headers.get("Origin")

        if origin and origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Vary"] = "Origin"
            response["Access-Control-Allow-Credentials"] = "true"

        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
