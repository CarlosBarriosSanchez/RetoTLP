from decimal import Decimal

from celery import shared_task
from django.utils import timezone

from apps.betting.models import Mercado, SeleccionMercado
from apps.betting.odds_broadcast import broadcast_odds_evento


@shared_task
def reactivar_mercado(mercado_id: int) -> None:
    Mercado.objects.filter(pk=mercado_id).update(suspendido_hasta=None)


@shared_task
def actualizar_cuota_seleccion(seleccion_id: int, nueva_cuota: str) -> None:
    """Tarea demo: cambia cuota y notifica por WebSocket."""
    from apps.betting.services import actualizar_cuota_seleccion as svc

    svc(seleccion_id, Decimal(nueva_cuota))
