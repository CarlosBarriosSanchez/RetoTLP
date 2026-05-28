from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.betting.models import (
    EstadoEvento,
    EventoDeportivo,
    Mercado,
    SeleccionMercado,
    TipoMercado,
)


def _crear_mercado_1x2(evento, local, visitante, o1, ox, o2):
    mercado = Mercado.objects.create(
        evento=evento, nombre="Resultado 1X2", tipo=TipoMercado.RESULTADO_1X2
    )
    SeleccionMercado.objects.bulk_create(
        [
            SeleccionMercado(mercado=mercado, etiqueta=f"Gana {local}", codigo="1", odds=o1),
            SeleccionMercado(mercado=mercado, etiqueta="Empate", codigo="X", odds=ox),
            SeleccionMercado(
                mercado=mercado, etiqueta=f"Gana {visitante}", codigo="2", odds=o2
            ),
        ]
    )


def _crear_ou25(evento):
    m = Mercado.objects.create(
        evento=evento, nombre="Más/Menos 2.5 goles", tipo=TipoMercado.OVER_UNDER_25
    )
    SeleccionMercado.objects.bulk_create(
        [
            SeleccionMercado(mercado=m, etiqueta="Más de 2.5", codigo="OVER", odds=Decimal("1.85")),
            SeleccionMercado(mercado=m, etiqueta="Menos de 2.5", codigo="UNDER", odds=Decimal("1.95")),
        ]
    )


def _crear_btts(evento):
    m = Mercado.objects.create(
        evento=evento, nombre="Ambos equipos anotan", tipo=TipoMercado.BTTS
    )
    SeleccionMercado.objects.bulk_create(
        [
            SeleccionMercado(mercado=m, etiqueta="Sí", codigo="SI", odds=Decimal("1.75")),
            SeleccionMercado(mercado=m, etiqueta="No", codigo="NO", odds=Decimal("2.05")),
        ]
    )


def _crear_handicap(evento, local):
    m = Mercado.objects.create(
        evento=evento, nombre="Hándicap asiático", tipo=TipoMercado.HANDICAP_ASIATICO
    )
    SeleccionMercado.objects.bulk_create(
        [
            SeleccionMercado(
                mercado=m, etiqueta=f"{local} -0.5", codigo="H1", odds=Decimal("1.90")
            ),
            SeleccionMercado(
                mercado=m, etiqueta=f"Visitante +0.5", codigo="H2", odds=Decimal("1.90")
            ),
        ]
    )


class Command(BaseCommand):
    help = "Crea eventos demo con mercados 1X2, O/U 2.5, BTTS y hándicap."

    def handle(self, *args, **options):
        if EventoDeportivo.objects.exists():
            self.stdout.write(self.style.WARNING("Ya hay eventos; omitiendo seed."))
            return

        partidos = [
            ("Perú vs Chile", "Perú", "Chile", Decimal("2.10"), Decimal("3.20"), Decimal("3.50")),
            ("Argentina vs Brasil", "Argentina", "Brasil", Decimal("2.80"), Decimal("3.10"), Decimal("2.45")),
            ("España vs Francia", "España", "Francia", Decimal("2.55"), Decimal("3.00"), Decimal("2.90")),
        ]
        inicio = timezone.now() + timedelta(days=2)

        for nombre, local, visitante, o1, ox, o2 in partidos:
            evento = EventoDeportivo.objects.create(
                nombre=nombre,
                equipo_local=local,
                equipo_visitante=visitante,
                inicio_programado=inicio,
                status=EstadoEvento.PROGRAMADO,
            )
            _crear_mercado_1x2(evento, local, visitante, o1, ox, o2)
            _crear_ou25(evento)
            _crear_btts(evento)
            _crear_handicap(evento, local)
            inicio += timedelta(hours=3)

        self.stdout.write(
            self.style.SUCCESS(
                f"Creados {len(partidos)} eventos con mercados 1X2, OU25, BTTS y AH."
            )
        )
