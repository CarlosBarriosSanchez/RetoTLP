from django.urls import path

from apps.audit.views import (
    VistaAlertasFraude,
    VistaDashboardOperador,
    VistaReporteMincetur,
    VistaVerificarAuditoria,
)

urlpatterns = [
    path("dashboard/", VistaDashboardOperador.as_view(), name="operador-dashboard"),
    path("auditoria/verificar/", VistaVerificarAuditoria.as_view(), name="auditoria-verificar"),
    path("reporte-mincetur/", VistaReporteMincetur.as_view(), name="reporte-mincetur"),
    path("alertas/", VistaAlertasFraude.as_view(), name="alertas-fraude"),
]
