import uuid

from django.conf import settings
from django.db import models


class LedgerAccount(models.TextChoices):
    """Cuentas contables del simulador (partida doble)."""

    WALLET_USUARIO = "wallet_usuario", "Wallet del usuario"
    CASA = "casa", "Casa / operador"
    APUESTAS_PENDIENTES = "apuestas_pendientes", "Fondos bloqueados en apuestas"
    BONOS = "bonos", "Bonos promocionales"


class EntryDirection(models.TextChoices):
    DEBIT = "DEBIT", "Débito"
    CREDIT = "CREDIT", "Crédito"


class LedgerTransaction(models.Model):
    """Agrupa entradas que deben balancearse (suma débitos = suma créditos)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=64)
    referencia = models.CharField(max_length=128, blank=True)
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.tipo} ({self.id})"


class LedgerEntry(models.Model):
    """
    Una línea del libro mayor. El saldo NUNCA se guarda aquí;
    se calcula sumando créditos menos débitos por cuenta.
    """

    transaction = models.ForeignKey(
        LedgerTransaction,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )
    account = models.CharField(max_length=32, choices=LedgerAccount.choices)
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    direction = models.CharField(max_length=8, choices=EntryDirection.choices)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "account"]),
            models.Index(fields=["account"]),
        ]

    def __str__(self):
        return f"{self.account} {self.direction} {self.amount}"
