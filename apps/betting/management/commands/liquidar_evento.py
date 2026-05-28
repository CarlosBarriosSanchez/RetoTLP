from django.core.management.base import BaseCommand, CommandError

from apps.betting.models import EstadoEvento, EventoDeportivo, SeleccionMercado
from apps.betting.services import ErrorApuesta, liquidar_evento


class Command(BaseCommand):
    help = (
        "Marca ganador, finaliza el evento y liquida apuestas aceptadas. "
        "Ej: python manage.py liquidar_evento --evento-id 1 --codigo 1"
    )

    def add_arguments(self, parser):
        parser.add_argument("--evento-id", type=int, required=True)
        parser.add_argument(
            "--codigo",
            type=str,
            help="Código ganador 1, X o 2 (omitir si el evento ya está anulado)",
        )

    def handle(self, *args, **options):
        try:
            evento = EventoDeportivo.objects.get(pk=options["evento_id"])
        except EventoDeportivo.DoesNotExist as e:
            raise CommandError("Evento no encontrado.") from e

        codigo = options.get("codigo")
        if evento.status == EstadoEvento.ANULADO:
            pass
        elif codigo:
            try:
                seleccion = SeleccionMercado.objects.get(
                    mercado__evento=evento, mercado__tipo="1X2", codigo=codigo.upper()
                )
            except SeleccionMercado.DoesNotExist as e:
                raise CommandError(f"No hay selección con código {codigo} en este evento.") from e
            evento.seleccion_ganadora = seleccion
            evento.status = EstadoEvento.FINALIZADO
            evento.save(update_fields=["seleccion_ganadora", "status"])
        elif not evento.seleccion_ganadora_id:
            raise CommandError("Indica --codigo 1, X o 2 o define ganador en el admin.")

        if evento.status != EstadoEvento.ANULADO and evento.status != EstadoEvento.FINALIZADO:
            evento.status = EstadoEvento.FINALIZADO
            evento.save(update_fields=["status"])

        try:
            stats = liquidar_evento(evento)
        except ErrorApuesta as e:
            raise CommandError(str(e)) from e

        self.stdout.write(
            self.style.SUCCESS(
                f"Liquidación OK — ganadas: {stats['ganadas']}, "
                f"perdidas: {stats['perdidas']}, anuladas: {stats['anuladas']}"
            )
        )
