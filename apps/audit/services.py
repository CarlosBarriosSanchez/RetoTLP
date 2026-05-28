from __future__ import annotations

import csv
import io
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.audit.models import RegistroAuditoria
from apps.betting.models import Apuesta, ApuestaCombinada, EstadoApuesta, EventoDeportivo, PiernaCombinada, SeleccionMercado
from apps.wallet.models import TransaccionContable

User = get_user_model()
HASH_GENESIS = "GENESIS"


@transaction.atomic
def registrar_auditoria(
    tipo_evento: str,
    payload: dict,
    referencia: str = "",
    usuario=None,
    ip_origen: str | None = None,
) -> RegistroAuditoria:
    ultimo = (
        RegistroAuditoria.objects.select_for_update()
        .order_by("-secuencia")
        .first()
    )
    secuencia = (ultimo.secuencia + 1) if ultimo else 1
    hash_anterior = ultimo.hash_registro if ultimo else HASH_GENESIS
    hash_registro = RegistroAuditoria.calcular_hash(
        hash_anterior, secuencia, tipo_evento, referencia, payload
    )
    return RegistroAuditoria.objects.create(
        secuencia=secuencia,
        tipo_evento=tipo_evento,
        referencia=referencia,
        payload=payload,
        hash_anterior=hash_anterior,
        hash_registro=hash_registro,
        ip_origen=ip_origen,
        usuario=usuario,
    )


def verificar_integridad_cadena() -> dict:
    registros = list(RegistroAuditoria.objects.order_by("secuencia"))
    hash_prev = HASH_GENESIS
    for reg in registros:
        if reg.hash_anterior != hash_prev:
            return {
                "valida": False,
                "registros": len(registros),
                "fallo_en_secuencia": reg.secuencia,
                "motivo": "hash_anterior no coincide",
            }
        esperado = RegistroAuditoria.calcular_hash(
            hash_prev, reg.secuencia, reg.tipo_evento, reg.referencia, reg.payload
        )
        if esperado != reg.hash_registro:
            return {
                "valida": False,
                "registros": len(registros),
                "fallo_en_secuencia": reg.secuencia,
                "motivo": "hash recalculado no coincide (posible alteración)",
            }
        hash_prev = reg.hash_registro
    return {"valida": True, "registros": len(registros), "ultimo_hash": hash_prev}


def _decimal_str(value) -> str:
    return str(Decimal(str(value or 0)).quantize(Decimal("0.0001")))


def metricas_operador(desde=None, hasta=None) -> dict:
    desde = desde or timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    hasta = hasta or timezone.now()

    filtro_ap = Q(creado_en__gte=desde, creado_en__lte=hasta)
    simples = Apuesta.objects.filter(filtro_ap)
    combinadas = ApuestaCombinada.objects.filter(filtro_ap)

    stakes_simples = simples.aggregate(t=Sum("stake"))["t"] or Decimal("0")
    stakes_combi = combinadas.aggregate(t=Sum("stake"))["t"] or Decimal("0")
    stakes_total = stakes_simples + stakes_combi

    payouts = Decimal("0")
    for a in simples.filter(status=EstadoApuesta.GANADA):
        payouts += a.payout_potencial
    for a in simples.filter(status=EstadoApuesta.CASHOUT):
        payouts += a.cashout_monto or Decimal("0")
    for c in combinadas.filter(status=EstadoApuesta.GANADA):
        payouts += c.payout_potencial

    ggr = (stakes_total - payouts).quantize(Decimal("0.0001"))
    usuarios_activos = (
        User.objects.filter(Q(apuestas__creado_en__range=(desde, hasta)) | Q(apuestas_combinadas__creado_en__range=(desde, hasta)))
        .distinct()
        .count()
    )

    exposure = []
    for ev in EventoDeportivo.objects.filter(apuesta__status=EstadoApuesta.ACEPTADA).distinct():
        filas = []
        for sel in SeleccionMercado.objects.filter(mercado__evento=ev, activo=True):
            exp = Decimal("0")
            for ap in Apuesta.objects.filter(evento=ev, status=EstadoApuesta.ACEPTADA, seleccion=sel):
                exp += ap.payout_potencial
            for pierna in PiernaCombinada.objects.filter(
                evento=ev,
                combinada__status=EstadoApuesta.ACEPTADA,
                seleccion=sel,
            ).select_related("combinada"):
                exp += pierna.combinada.payout_potencial
            if exp > 0:
                filas.append({"seleccion": sel.etiqueta, "exposure": _decimal_str(exp)})
        if filas:
            exposure.append({"evento": str(ev), "selecciones": filas})

    alertas_pendientes = __import__(
        "apps.audit.models", fromlist=["ActividadSospechosa"]
    ).ActividadSospechosa.objects.filter(resuelta=False).count()

    return {
        "periodo": {"desde": desde.isoformat(), "hasta": hasta.isoformat()},
        "volumen_apuestas": simples.count() + combinadas.count(),
        "stakes_total": _decimal_str(stakes_total),
        "payouts_total": _decimal_str(payouts),
        "ggr": _decimal_str(ggr),
        "usuarios_activos": usuarios_activos,
        "exposure_por_evento": exposure,
        "alertas_fraude_pendientes": alertas_pendientes,
    }


def generar_csv_mincetur(anio: int, mes: int) -> str:
    """Reporte mensual educativo estilo MINCETUR (CSV)."""
    inicio = timezone.make_aware(datetime(anio, mes, 1))
    if mes == 12:
        fin = timezone.make_aware(datetime(anio + 1, 1, 1))
    else:
        fin = timezone.make_aware(datetime(anio, mes + 1, 1))

    m = metricas_operador(inicio, fin - timezone.timedelta(microseconds=1))
    tx_wallet = TransaccionContable.objects.filter(creado_en__gte=inicio, creado_en__lt=fin).count()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "periodo",
            "operador",
            "total_apuestas",
            "monto_apostado_pen",
            "total_payouts_pen",
            "ggr_pen",
            "usuarios_activos",
            "transacciones_wallet",
            "moneda",
            "nota_legal",
        ]
    )
    writer.writerow(
        [
            f"{anio}-{mes:02d}",
            "FairBet Lab (educativo)",
            m["volumen_apuestas"],
            m["stakes_total"],
            m["payouts_total"],
            m["ggr"],
            m["usuarios_activos"],
            tx_wallet,
            "PEN virtual",
            "Simulador sin dinero real — Ley 31557 referencial",
        ]
    )
    return buffer.getvalue()
