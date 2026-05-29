from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView


def health_check(request):
    """Comprueba que el servidor responde (útil con Docker)."""
    return JsonResponse(
        {
            "status": "ok",
            "proyecto": "FairBet Lab",
            "mensaje": "Entorno educativo — moneda virtual",
        }
    )


urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("cuenta/", TemplateView.as_view(template_name="cuenta.html"), name="cuenta"),
    path("cartera/", TemplateView.as_view(template_name="cartera.html"), name="cartera"),
    path("eventos/", TemplateView.as_view(template_name="eventos.html"), name="eventos"),
    path("apuestas/", TemplateView.as_view(template_name="apuestas.html"), name="apuestas"),
    path("operador/", TemplateView.as_view(template_name="operador.html"), name="operador"),
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health"),
    path("api/users/", include("apps.users.urls")),
    path("api/wallet/", include("apps.wallet.urls")),
    path("api/operador/", include("apps.audit.urls")),
    path("api/", include("apps.betting.urls")),
]
