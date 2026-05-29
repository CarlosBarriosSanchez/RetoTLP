import hashlib
import json

from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    """
    Libro append-only con encadenamiento SHA256:
    hash_n = SHA256(hash_{n-1} + payload_canónico)
    """

    secuencia = models.PositiveBigIntegerField(unique=True)
    tipo_evento = models.CharField(max_length=64, verbose_name="tipo de evento")
    referencia = models.CharField(max_length=128, blank=True)
    payload = models.JSONField(default=dict)
    hash_anterior = models.CharField(max_length=64)
    hash_registro = models.CharField(max_length=64, unique=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_auditoria",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["secuencia"]
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"

    def __str__(self):
        return f"#{self.secuencia} {self.tipo_evento}"

    @staticmethod
    def calcular_hash(hash_anterior: str, secuencia: int, tipo: str, referencia: str, payload: dict) -> str:
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        contenido = f"{hash_anterior}|{secuencia}|{tipo}|{referencia}|{payload_str}"
        return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


class TipoAlerta(models.TextChoices):
    MULTIPLES_CUENTAS_IP = "multiples_cuentas_ip", "Varias cuentas desde la misma IP"
    DEPOSITO_CASHOUT_RAPIDO = "deposito_cashout_rapido", "Depósito seguido de cash-out rápido"
    APUESTAS_ESPEJO = "apuestas_espejo", "Patrón de apuestas espejo"
    ABUSO_BONO = "abuso_bono", "Intentos de abuso de bono"


class SeveridadAlerta(models.TextChoices):
    BAJA = "baja", "Baja"
    MEDIA = "media", "Media"
    ALTA = "alta", "Alta"


class ActividadSospechosa(models.Model):
    """Alertas anti-fraude para revisión manual del operador."""

    tipo = models.CharField(max_length=48, choices=TipoAlerta.choices)
    severidad = models.CharField(
        max_length=16,
        choices=SeveridadAlerta.choices,
        default=SeveridadAlerta.MEDIA,
    )
    descripcion = models.TextField()
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alertas_fraude",
    )
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    resuelta = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Actividad sospechosa"
        verbose_name_plural = "Actividades sospechosas"

    def __str__(self):
        return f"{self.get_tipo_display()} ({self.severidad})"
