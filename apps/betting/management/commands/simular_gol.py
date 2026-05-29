from django.core.management.base import BaseCommand, CommandError

from apps.betting.models import Mercado, TipoMercado
from apps.betting.services import suspender_mercado_por_evento_critico


class Command(BaseCommand):
    help = "Simula gol/expulsión: suspende mercados 1X2 del evento N segundos y notifica por WS."

    def add_arguments(self, parser):
        parser.add_argument("--evento-id", type=int, required=True)
        parser.add_argument("--segundos", type=int, default=30)

    def handle(self, *args, **options):
        mercados = Mercado.objects.filter(
            evento_id=options["evento_id"], tipo=TipoMercado.RESULTADO_1X2
        )
        if not mercados.exists():
            raise CommandError("No hay mercado 1X2 para ese evento.")

        for mercado in mercados:
            suspender_mercado_por_evento_critico(mercado.id, options["segundos"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Mercados 1X2 suspendidos {options['segundos']}s (in-play). "
                "Conecta WebSocket ws://localhost:8001/ws/eventos/<id>/odds/"
            )
        )
