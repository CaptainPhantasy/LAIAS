from collections.abc import Mapping
from typing import cast

from starlette.types import ASGIApp, Message, Receive, Scope, Send

DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
}


class SecurityHeadersMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        headers: Mapping[str, str] | None = None,
        hsts_enabled: bool = True,
        hsts_value: str = "max-age=31536000; includeSubDomains",
        trust_proxy_headers: bool = True,
    ) -> None:
        self._app: ASGIApp = app
        self._headers: dict[str, str] = dict(headers or DEFAULT_SECURITY_HEADERS)
        self._encoded_headers: list[tuple[bytes, bytes]] = [
            (key.lower().encode("latin-1"), value.encode("latin-1"))
            for key, value in self._headers.items()
        ]
        self._hsts_enabled: bool = hsts_enabled
        self._hsts_value: str = hsts_value
        self._hsts_encoded: tuple[bytes, bytes] = (
            b"strict-transport-security",
            self._hsts_value.encode("latin-1"),
        )
        self._trust_proxy_headers: bool = trust_proxy_headers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message.get("type") != "http.response.start":
                await send(message)
                return

            raw_headers = message.get("headers")
            response_headers: list[tuple[bytes, bytes]] = []
            if isinstance(raw_headers, list):
                response_headers = cast(list[tuple[bytes, bytes]], raw_headers.copy())
            header_keys = {key.lower() for key, _ in response_headers}

            for key, value in self._encoded_headers:
                if key not in header_keys:
                    response_headers.append((key, value))

            if (
                self._hsts_enabled
                and self._should_set_hsts(scope)
                and self._hsts_encoded[0] not in header_keys
            ):
                response_headers.append(self._hsts_encoded)

            message["headers"] = response_headers
            await send(message)

        await self._app(scope, receive, send_with_headers)

    def _should_set_hsts(self, scope: Scope) -> bool:
        hostname = self._resolve_hostname(scope)
        if self._is_local_hostname(hostname):
            return False

        if self._trust_proxy_headers:
            forwarded_proto = self._get_header(scope, b"x-forwarded-proto")
            if forwarded_proto:
                return forwarded_proto.split(",", maxsplit=1)[0].strip().lower() == "https"

        scheme = scope.get("scheme")
        return isinstance(scheme, str) and scheme.lower() == "https"

    def _resolve_hostname(self, scope: Scope) -> str:
        host_value = ""
        if self._trust_proxy_headers:
            host_value = self._get_header(scope, b"x-forwarded-host")
            if host_value:
                host_value = host_value.split(",", maxsplit=1)[0].strip()

        if not host_value:
            host_value = self._get_header(scope, b"host")

        hostname = host_value.split(":", maxsplit=1)[0].strip().lower()
        return hostname

    @staticmethod
    def _get_header(scope: Scope, key: bytes) -> str:
        for header_key, value in SecurityHeadersMiddleware._scope_headers(scope):
            if header_key == key:
                return value.decode("latin-1")
        return ""

    @staticmethod
    def _scope_headers(scope: Scope) -> list[tuple[bytes, bytes]]:
        return cast(list[tuple[bytes, bytes]], scope.get("headers", []))

    @staticmethod
    def _is_local_hostname(hostname: str) -> bool:
        return hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".localhost")
