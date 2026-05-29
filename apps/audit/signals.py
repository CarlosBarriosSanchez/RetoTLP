from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit.antifraude import evaluar_apuestas_espejo, evaluar_deposito_seguido_cashout
from apps.audit.context import get_client_ip
from apps.audit.services import registrar_auditoria
from apps.betting.models import Apuesta, ApuestaCombinada, SeleccionMercado
from apps.wallet.models import TransaccionContable


@receiver(post_save, sender=TransaccionContable)
def auditar_transaccion_wallet(sender, instance, created, **kwargs):
    if not created:
        return
    registrar_auditoria(
        tipo_evento="wallet_tx",
        referencia=str(instance.id),
        payload={
            "tipo": instance.tipo,
            "referencia": instance.referencia,
            "idempotency_key": instance.idempotency_key,
        },
        ip_origen=get_client_ip(),
    )


@receiver(post_save, sender=Apuesta)
def auditar_apuesta(sender, instance, created, **kwargs):
    if created:
        registrar_auditoria(
            tipo_evento="apuesta_simple",
            referencia=str(instance.id),
            payload={
                "evento_id": instance.evento_id,
                "seleccion_id": instance.seleccion_id,
                "stake": str(instance.stake),
                "odds_locked": str(instance.odds_locked),
                "status": instance.status,
            },
            usuario=instance.user,
            ip_origen=get_client_ip(),
        )
        evaluar_apuestas_espejo(instance)
    elif instance.status == "cashout":
        registrar_auditoria(
            tipo_evento="cashout",
            referencia=str(instance.id),
            payload={
                "cashout_monto": str(instance.cashout_monto or 0),
                "stake": str(instance.stake),
            },
            usuario=instance.user,
            ip_origen=get_client_ip(),
        )
        evaluar_deposito_seguido_cashout(instance.user)


@receiver(post_save, sender=ApuestaCombinada)
def auditar_combinada(sender, instance, created, **kwargs):
    if not created:
        return
    registrar_auditoria(
        tipo_evento="apuesta_combinada",
        referencia=str(instance.id),
        payload={
            "stake": str(instance.stake),
            "odds_locked": str(instance.odds_locked),
        },
        usuario=instance.user,
        ip_origen=get_client_ip(),
    )


@receiver(post_save, sender=SeleccionMercado)
def auditar_cambio_cuota(sender, instance, created, **kwargs):
    if created:
        return
    if not kwargs.get("update_fields") or "odds" in kwargs.get("update_fields", {}):
        registrar_auditoria(
            tipo_evento="cambio_cuota",
            referencia=str(instance.id),
            payload={
                "mercado_id": instance.mercado_id,
                "etiqueta": instance.etiqueta,
                "odds": str(instance.odds),
            },
            ip_origen=get_client_ip(),
        )
