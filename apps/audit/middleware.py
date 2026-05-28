from apps.audit.context import set_client_ip


class ClientIPMiddleware:
    """Expone la IP del cliente para auditoría y anti-fraude."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        set_client_ip(ip)
        return self.get_response(request)
