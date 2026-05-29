import contextvars

_client_ip: contextvars.ContextVar[str | None] = contextvars.ContextVar("client_ip", default=None)


def set_client_ip(ip: str | None) -> None:
    _client_ip.set(ip)


def get_client_ip() -> str | None:
    return _client_ip.get()
