from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.betting.models import SeleccionMercado
from apps.betting.services import actualizar_cuota_seleccion


class Command(BaseCommand):
    help = "Actualiza cuota de una selección y notifica por Channels."

    def add_arguments(self, parser):
        parser.add_argument("--seleccion-id", type=int, required=True)
        parser.add_argument("--odds", type=str, required=True)

    def handle(self, *args, **options):
        try:
            sel = SeleccionMercado.objects.get(pk=options["seleccion_id"])
        except SeleccionMercado.DoesNotExist as e:
            raise CommandError("Selección no encontrada.") from e

        actualizar_cuota_seleccion(sel.id, Decimal(options["odds"]))
        self.stdout.write(self.style.SUCCESS(f"Cuota actualizada: {sel.etiqueta} @ {options['odds']}"))
