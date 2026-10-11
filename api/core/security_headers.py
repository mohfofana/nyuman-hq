from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Ce que la page a le droit de charger : elle-même, les polices Google, et le bouton Google (facultatif).
_CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' https://accounts.google.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: blob:",
        "connect-src 'self' https://accounts.google.com",
        "frame-src https://accounts.google.com",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ]
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """HQ est privé : jamais dans un moteur de recherche, jamais affiché dans le cadre d'un autre site."""

    def __init__(self, app, production: bool):
        super().__init__(app)
        self._production = production

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Robots-Tag", "noindex, nofollow, noarchive")
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "same-origin")
        headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        headers.setdefault("Content-Security-Policy", _CSP)
        if self._production:
            headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        # La page d'accueil est relue à chaque visite (les fichiers de l'interface, eux, changent de nom à chaque version).
        if not request.url.path.startswith(("/api/", "/assets/")) and "text/html" in headers.get("content-type", ""):
            headers["Cache-Control"] = "no-cache"
        return response
