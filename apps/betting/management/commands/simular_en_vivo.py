from django.core.management.base import BaseCommand, CommandError

from apps.betting.models import EstadoEvento, EventoDeportivo


class Command(BaseCommand):
    help = "Pone un evento en estado en_vivo (permite apuestas in-play)."

    def add_arguments(self, parser):
        parser.add_argument("--evento-id", type=int, required=True)

    def handle(self, *args, **options):
        try:
            evento = EventoDeportivo.objects.get(pk=options["evento_id"])
        except EventoDeportivo.DoesNotExist as e:
            raise CommandError("Evento no encontrado.") from e

        evento.status = EstadoEvento.EN_VIVO
        evento.save(update_fields=["status"])
        self.stdout.write(self.style.SUCCESS(f"{evento} ahora está EN VIVO."))
