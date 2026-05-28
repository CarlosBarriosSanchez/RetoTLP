from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import ActividadSospechosa
from apps.audit.services import generar_csv_mincetur, metricas_operador, verificar_integridad_cadena


class EsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class VistaDashboardOperador(APIView):
    permission_classes = [EsStaff]

    def get(self, request):
        return Response(metricas_operador())


class VistaVerificarAuditoria(APIView):
    permission_classes = [EsStaff]

    def get(self, request):
        resultado = verificar_integridad_cadena()
        code = status.HTTP_200_OK if resultado["valida"] else status.HTTP_409_CONFLICT
        return Response(resultado, status=code)


class VistaReporteMincetur(APIView):
    permission_classes = [EsStaff]

    def get(self, request):
        try:
            anio = int(request.query_params.get("anio", 2026))
            mes = int(request.query_params.get("mes", 5))
        except (TypeError, ValueError):
            return Response({"error": "Parámetros anio y mes inválidos."}, status=400)
        if mes < 1 or mes > 12:
            return Response({"error": "Mes debe estar entre 1 y 12."}, status=400)
        csv_data = generar_csv_mincetur(anio, mes)
        response = HttpResponse(csv_data, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="fairbet_mincetur_{anio}_{mes:02d}.csv"'
        return response


class VistaAlertasFraude(APIView):
    permission_classes = [EsStaff]

    def get(self, request):
        alertas = ActividadSospechosa.objects.filter(resuelta=False)[:50]
        data = [
            {
                "id": a.id,
                "tipo": a.tipo,
                "severidad": a.severidad,
                "descripcion": a.descripcion,
                "usuario": a.usuario.username if a.usuario else None,
                "ip_origen": a.ip_origen,
                "creado_en": a.creado_en.isoformat(),
            }
            for a in alertas
        ]
        return Response({"alertas": data})
