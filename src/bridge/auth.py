from fastapi import Request


async def require_local_request(request: Request) -> None:
    """Placeholder for future token/origin checks.

    The MVP exposes only read/analyse operations, but production pairing must add
    a short-lived local token and strict SaaS origin allowlist before broad use.
    """
    client = request.client
    if client is None:
        return
    # TestClient reports "testclient"; live deployments should bind to 127.0.0.1.
    if client.host in {"127.0.0.1", "::1", "testclient"}:
        return
