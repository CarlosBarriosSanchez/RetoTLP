from django.core.management.base import BaseCommand

from apps.audit.services import verificar_integridad_cadena


class Command(BaseCommand):
    help = "Verifica la integridad de la cadena hash de auditoría."

    def handle(self, *args, **options):
        resultado = verificar_integridad_cadena()
        if resultado["valida"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Cadena OK — {resultado['registros']} registros, "
                    f"último hash: {resultado.get('ultimo_hash', '—')[:16]}…"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"Cadena INVÁLIDA en secuencia #{resultado.get('fallo_en_secuencia')}: "
                    f"{resultado.get('motivo')}"
                )
            )
