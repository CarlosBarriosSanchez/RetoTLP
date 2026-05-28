from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.betting.models import (
    Apuesta,
    ApuestaCombinada,
    EstadoApuesta,
    EstadoEvento,
    EventoDeportivo,
    Mercado,
    PiernaCombinada,
    SeleccionMercado,
    TipoMercado,
)
from apps.betting.odds_broadcast import broadcast_odds_evento
from apps.wallet import services as servicios_wallet
from apps.wallet.services import ErrorWallet

STAKE_MIN = Decimal("1.0000")
STAKE_MAX = Decimal("500.0000")


class ErrorApuesta(Exception):
    pass


class RequoteRequired(ErrorApuesta):
    """La cuota cambió; el cliente debe reconfirmar con la nueva cuota."""

    def __init__(self, nueva_cuota: Decimal, mensaje: str | None = None):
        self.nueva_cuota = nueva_cuota
        super().__init__(
            mensaje
            or f"La cuota cambió a {nueva_cuota}. Reconfirma la apuesta con odds_esperada."
        )


def _validar_usuario_puede_apostar(user) -> None:
    perfil = user.perfil
    if perfil.esta_autoexcluido:
        raise ErrorApuesta("Cuenta autoexcluida: no puede apostar.")
    if not perfil.puede_apostar:
        raise ErrorApuesta("Cuenta no verificada. Completa KYC simulado.")


def _validar_seleccion_disponible(seleccion: SeleccionMercado, evento: EventoDeportivo) -> None:
    if seleccion.mercado.evento_id != evento.id:
        raise ErrorApuesta("La selección no pertenece a este evento.")
    if not seleccion.activo:
        raise ErrorApuesta("Selección no disponible.")
    if not seleccion.mercado.esta_disponible:
        raise ErrorApuesta("Mercado suspendido temporalmente (in-play). Intenta en unos segundos.")


def _validar_requote(seleccion: SeleccionMercado, odds_esperada: Decimal | None, confirmar: bool) -> None:
    if odds_esperada is None:
        return
    odds_esperada = Decimal(str(odds_esperada)).quantize(Decimal("0.01"))
    actual = Decimal(str(seleccion.odds)).quantize(Decimal("0.01"))
    if actual != odds_esperada and not confirmar:
        raise RequoteRequired(actual)


def validar_piernas_combinada(selecciones: list[SeleccionMercado]) -> None:
    """
    Permite combinar mercados distintos del mismo partido (ej. 1X2 + BTTS).
    No permite dos selecciones del mismo mercado (ej. Gana Perú + Empate).
    """
    if len(selecciones) < 2:
        raise ErrorApuesta("La apuesta combinada requiere al menos 2 selecciones.")

    mercados_vistos: set[int] = set()
    for sel in selecciones:
        mid = sel.mercado_id
        if mid in mercados_vistos:
            raise ErrorApuesta(
                "No puedes combinar dos opciones del mismo mercado "
                "(ej. Gana Perú y Empate en el mismo 1X2)."
            )
        mercados_vistos.add(mid)


def _pierna_combinada_ganadora(pierna: PiernaCombinada) -> bool | None:
    """True ganada, False perdida, None si el mercado aún no tiene resultado."""
    return _seleccion_es_ganadora(pierna.seleccion, pierna.evento)


def _seleccion_es_ganadora(seleccion: SeleccionMercado, evento: EventoDeportivo) -> bool | None:
    mercado = seleccion.mercado
    if mercado.tipo == TipoMercado.RESULTADO_1X2:
        if not evento.seleccion_ganadora_id:
            return None
        return seleccion.id == evento.seleccion_ganadora_id
    if mercado.seleccion_ganadora_id:
        return seleccion.id == mercado.seleccion_ganadora_id
    return None


def mercados_sin_ganador_para_liquidacion(evento: EventoDeportivo) -> list[Mercado]:
    """Mercados con apuestas aceptadas que aún no tienen selección ganadora."""
    mercado_ids: set[int] = set()

    apuestas = Apuesta.objects.filter(
        evento=evento, status=EstadoApuesta.ACEPTADA
    ).select_related("seleccion__mercado")
    for apuesta in apuestas:
        mercado = apuesta.seleccion.mercado
        if mercado.tipo != TipoMercado.RESULTADO_1X2:
            mercado_ids.add(mercado.id)

    piernas = PiernaCombinada.objects.filter(
        evento=evento, combinada__status=EstadoApuesta.ACEPTADA
    ).select_related("seleccion__mercado")
    for pierna in piernas:
        mercado = pierna.seleccion.mercado
        if mercado.tipo != TipoMercado.RESULTADO_1X2:
            mercado_ids.add(mercado.id)

    if not evento.seleccion_ganadora_id:
        for apuesta in apuestas:
            if apuesta.seleccion.mercado.tipo == TipoMercado.RESULTADO_1X2:
                mercado_ids.add(apuesta.seleccion.mercado_id)
        for pierna in piernas:
            if pierna.seleccion.mercado.tipo == TipoMercado.RESULTADO_1X2:
                mercado_ids.add(pierna.seleccion.mercado_id)

    if not mercado_ids:
        return []

    return list(
        Mercado.objects.filter(pk__in=mercado_ids, seleccion_ganadora__isnull=True).order_by(
            "nombre"
        )
    )


@transaction.atomic
def colocar_apuesta_simple(
    user,
    evento: EventoDeportivo,
    seleccion: SeleccionMercado,
    stake: Decimal,
    idempotency_key: str | None = None,
    odds_esperada: Decimal | None = None,
    confirmar_requote: bool = False,
) -> Apuesta:
    """Apuesta simple (pre-partido o in-play) con política de re-cotización."""
    if idempotency_key and Apuesta.objects.filter(idempotency_key=idempotency_key).exists():
        return Apuesta.objects.get(idempotency_key=idempotency_key)

    _validar_usuario_puede_apostar(user)

    if not evento.acepta_apuestas:
        raise ErrorApuesta("El evento no acepta apuestas en este momento.")

    _validar_seleccion_disponible(seleccion, evento)
    _validar_requote(seleccion, odds_esperada, confirmar_requote)

    stake = Decimal(str(stake)).quantize(Decimal("0.0001"))
    if stake < STAKE_MIN or stake > STAKE_MAX:
        raise ErrorApuesta(f"Monto fuera de límites ({STAKE_MIN} — {STAKE_MAX}).")

    apuesta = Apuesta(
        user=user,
        evento=evento,
        seleccion=seleccion,
        stake=stake,
        odds_locked=seleccion.odds,
        status=EstadoApuesta.ACEPTADA,
        idempotency_key=idempotency_key,
    )
    apuesta.save()

    try:
        tx = servicios_wallet.bloquear_fondos_apuesta(
            user,
            stake,
            apuesta_id=str(apuesta.id),
            idempotency_key=f"bet-lock-{apuesta.id}" if idempotency_key else None,
        )
    except ErrorWallet as e:
        apuesta.delete()
        raise ErrorApuesta(str(e)) from e

    apuesta.transaccion_contable = tx
    apuesta.save(update_fields=["transaccion_contable"])
    servicios_wallet.registrar_apuesta_para_rollover(user, stake)
    return apuesta


@transaction.atomic
def colocar_apuesta_combinada(
    user,
    selection_ids: list[int],
    stake: Decimal,
    idempotency_key: str | None = None,
) -> ApuestaCombinada:
    if idempotency_key and ApuestaCombinada.objects.filter(idempotency_key=idempotency_key).exists():
        return ApuestaCombinada.objects.get(idempotency_key=idempotency_key)

    _validar_usuario_puede_apostar(user)

    selecciones = list(
        SeleccionMercado.objects.select_related("mercado__evento").filter(pk__in=selection_ids)
    )
    if len(selecciones) != len(set(selection_ids)):
        raise ErrorApuesta("Alguna selección no existe.")

    validar_piernas_combinada(selecciones)

    cuota_final = Decimal("1.00")
    for sel in selecciones:
        evento = sel.mercado.evento
        if not evento.acepta_apuestas:
            raise ErrorApuesta(f"{evento} no acepta apuestas ahora.")
        _validar_seleccion_disponible(sel, evento)
        cuota_final *= Decimal(str(sel.odds))

    cuota_final = cuota_final.quantize(Decimal("0.0001"))
    stake = Decimal(str(stake)).quantize(Decimal("0.0001"))
    if stake < STAKE_MIN or stake > STAKE_MAX:
        raise ErrorApuesta(f"Monto fuera de límites ({STAKE_MIN} — {STAKE_MAX}).")

    combinada = ApuestaCombinada(
        user=user,
        stake=stake,
        odds_locked=cuota_final,
        status=EstadoApuesta.ACEPTADA,
        idempotency_key=idempotency_key,
    )
    combinada.save()

    try:
        tx = servicios_wallet.bloquear_fondos_apuesta(
            user,
            stake,
            apuesta_id=str(combinada.id),
            idempotency_key=f"combo-lock-{combinada.id}" if idempotency_key else None,
        )
    except ErrorWallet as e:
        combinada.delete()
        raise ErrorApuesta(str(e)) from e

    combinada.transaccion_contable = tx
    combinada.save(update_fields=["transaccion_contable"])
    servicios_wallet.registrar_apuesta_para_rollover(user, stake)

    for sel in selecciones:
        PiernaCombinada.objects.create(
            combinada=combinada,
            evento=sel.mercado.evento,
            seleccion=sel,
            odds_locked=sel.odds,
        )
    return combinada


def calcular_cashout(apuesta: Apuesta) -> Decimal:
    """
    cashout = stake × odds_original / odds_actual × factor_casa
  """
    if apuesta.status != EstadoApuesta.ACEPTADA:
        raise ErrorApuesta("Solo apuestas aceptadas pueden hacer cash-out.")
    odds_actual = Decimal(str(apuesta.seleccion.odds))
    if odds_actual <= 0:
        raise ErrorApuesta("Cuota actual inválida.")
    factor = settings.CASHOUT_FACTOR_CASA
    monto = (
        Decimal(str(apuesta.stake))
        * Decimal(str(apuesta.odds_locked))
        / odds_actual
        * factor
    )
    return monto.quantize(Decimal("0.0001"))


@transaction.atomic
def ejecutar_cashout_apuesta(apuesta: Apuesta, idempotency_key: str | None = None) -> Apuesta:
    apuesta = Apuesta.objects.select_for_update().get(pk=apuesta.pk)
    if apuesta.status != EstadoApuesta.ACEPTADA:
        raise ErrorApuesta("La apuesta ya no está activa.")

    monto = calcular_cashout(apuesta)
    servicios_wallet.ejecutar_cashout(
        apuesta.user,
        monto,
        apuesta.stake,
        str(apuesta.id),
        idempotency_key=idempotency_key or f"cashout-{apuesta.id}",
    )
    apuesta.status = EstadoApuesta.CASHOUT
    apuesta.cashout_monto = monto
    apuesta.cashout_en = timezone.now()
    apuesta.save(update_fields=["status", "cashout_monto", "cashout_en"])
    return apuesta


@transaction.atomic
def actualizar_cuota_seleccion(seleccion_id: int, nueva_cuota: Decimal) -> SeleccionMercado:
    seleccion = SeleccionMercado.objects.select_for_update().select_related("mercado__evento").get(
        pk=seleccion_id
    )
    seleccion.odds = Decimal(str(nueva_cuota)).quantize(Decimal("0.01"))
    seleccion.save(update_fields=["odds"])
    evento = seleccion.mercado.evento
    broadcast_odds_evento(
        evento.id,
        {
            "tipo": "odds_update",
            "evento_id": evento.id,
            "selection_id": seleccion.id,
            "mercado_id": seleccion.mercado_id,
            "odds": str(seleccion.odds),
            "etiqueta": seleccion.etiqueta,
        },
    )
    return seleccion


@transaction.atomic
def suspender_mercado_por_evento_critico(mercado_id: int, segundos: int | None = None) -> Mercado:
    """In-play: suspende mercado N segundos (gol, expulsión) y notifica por WS."""
    segundos = segundos or settings.MERCADO_SUSPENSION_SEGUNDOS
    mercado = Mercado.objects.select_for_update().select_related("evento").get(pk=mercado_id)
    mercado.suspendido_hasta = timezone.now() + timezone.timedelta(seconds=segundos)
    mercado.save(update_fields=["suspendido_hasta"])

    from apps.betting.tasks import reactivar_mercado

    reactivar_mercado.apply_async(args=[mercado.id], countdown=segundos)

    broadcast_odds_evento(
        mercado.evento_id,
        {
            "tipo": "mercado_suspendido",
            "evento_id": mercado.evento_id,
            "mercado_id": mercado.id,
            "suspendido_hasta": mercado.suspendido_hasta.isoformat(),
            "segundos": segundos,
        },
    )
    return mercado


@transaction.atomic
def registrar_evento_critico_inplay(
    evento_id: int,
    descripcion: str = "Evento crítico",
    segundos: int | None = None,
) -> EventoDeportivo:
    """Simula un evento crítico in-play, como expulsión, y suspende el mercado 1X2."""
    evento = EventoDeportivo.objects.select_for_update().get(pk=evento_id)
    if evento.status in (EstadoEvento.FINALIZADO, EstadoEvento.ANULADO):
        raise ErrorApuesta("No se puede registrar evento crítico en un evento finalizado o anulado.")

    if evento.status == EstadoEvento.PROGRAMADO:
        evento.status = EstadoEvento.EN_VIVO
        evento.save(update_fields=["status"])

    segundos = segundos or settings.MERCADO_SUSPENSION_SEGUNDOS
    mercados = Mercado.objects.filter(evento=evento, tipo=TipoMercado.RESULTADO_1X2)
    for mercado in mercados:
        suspender_mercado_por_evento_critico(mercado.id, segundos=segundos)

    broadcast_odds_evento(
        evento.id,
        {
            "tipo": "evento_critico",
            "evento_id": evento.id,
            "descripcion": descripcion,
            "segundos_suspension": segundos,
        },
    )
    return evento


def _cuota(valor: str) -> Decimal:
    return Decimal(valor).quantize(Decimal("0.01"))


def _cuotas_1x2_por_marcador(evento: EventoDeportivo) -> dict[str, Decimal]:
    diferencia = evento.goles_local - evento.goles_visitante
    total_goles = evento.goles_local + evento.goles_visitante

    if diferencia > 0:
        return {
            "1": max(_cuota("1.10"), _cuota("1.75") - _cuota("0.25") * diferencia),
            "X": min(_cuota("8.00"), _cuota("3.40") + _cuota("0.45") * diferencia),
            "2": min(_cuota("15.00"), _cuota("4.00") + _cuota("1.20") * diferencia),
        }
    if diferencia < 0:
        ventaja = abs(diferencia)
        return {
            "1": min(_cuota("15.00"), _cuota("4.00") + _cuota("1.20") * ventaja),
            "X": min(_cuota("8.00"), _cuota("3.40") + _cuota("0.45") * ventaja),
            "2": max(_cuota("1.10"), _cuota("1.75") - _cuota("0.25") * ventaja),
        }
    if total_goles:
        return {"1": _cuota("2.80"), "X": _cuota("2.55"), "2": _cuota("2.80")}
    return {}


def _cuotas_ou25_por_marcador(evento: EventoDeportivo) -> dict[str, Decimal]:
    total_goles = evento.goles_local + evento.goles_visitante
    if total_goles >= 3:
        return {"OVER": _cuota("1.05"), "O": _cuota("1.05"), "UNDER": _cuota("12.00"), "U": _cuota("12.00")}
    if total_goles == 2:
        return {"OVER": _cuota("1.35"), "O": _cuota("1.35"), "UNDER": _cuota("3.20"), "U": _cuota("3.20")}
    if total_goles == 1:
        return {"OVER": _cuota("1.75"), "O": _cuota("1.75"), "UNDER": _cuota("2.05"), "U": _cuota("2.05")}
    return {}


def _cuotas_btts_por_marcador(evento: EventoDeportivo) -> dict[str, Decimal]:
    ambos_anotaron = evento.goles_local > 0 and evento.goles_visitante > 0
    alguien_anoto = evento.goles_local > 0 or evento.goles_visitante > 0
    if ambos_anotaron:
        return {"SI": _cuota("1.05"), "S": _cuota("1.05"), "YES": _cuota("1.05"), "NO": _cuota("12.00")}
    if alguien_anoto:
        return {"SI": _cuota("1.55"), "S": _cuota("1.55"), "YES": _cuota("1.55"), "NO": _cuota("2.40")}
    return {}


def recalcular_cuotas_inplay(evento: EventoDeportivo) -> list[SeleccionMercado]:
    """Ajuste simple para demo: las cuotas cambian según el marcador en vivo."""
    reglas_por_tipo = {
        TipoMercado.RESULTADO_1X2: _cuotas_1x2_por_marcador(evento),
        TipoMercado.OVER_UNDER_25: _cuotas_ou25_por_marcador(evento),
        TipoMercado.BTTS: _cuotas_btts_por_marcador(evento),
    }
    actualizadas = []
    selecciones = SeleccionMercado.objects.select_for_update().select_related("mercado").filter(
        mercado__evento=evento,
        mercado__tipo__in=reglas_por_tipo.keys(),
        activo=True,
    )
    for seleccion in selecciones:
        nueva_cuota = reglas_por_tipo.get(seleccion.mercado.tipo, {}).get(seleccion.codigo.upper())
        if nueva_cuota is None or seleccion.odds == nueva_cuota:
            continue
        seleccion.odds = nueva_cuota
        seleccion.save(update_fields=["odds"])
        actualizadas.append(seleccion)
        broadcast_odds_evento(
            evento.id,
            {
                "tipo": "odds_update",
                "evento_id": evento.id,
                "selection_id": seleccion.id,
                "mercado_id": seleccion.mercado_id,
                "odds": str(seleccion.odds),
                "etiqueta": seleccion.etiqueta,
            },
        )
    return actualizadas


@transaction.atomic
def registrar_gol_evento(evento_id: int, lado: str, segundos: int | None = None) -> EventoDeportivo:
    """
    Demo in-play: registra gol local/visitante, pone el evento en vivo,
    suspende mercados 1X2 y notifica por WebSocket.
    """
    evento = EventoDeportivo.objects.select_for_update().get(pk=evento_id)
    if evento.status in (EstadoEvento.FINALIZADO, EstadoEvento.ANULADO):
        raise ErrorApuesta("No se puede registrar gol en un evento finalizado o anulado.")

    lado = lado.lower()
    if lado == "local":
        evento.goles_local += 1
        equipo_gol = evento.equipo_local
    elif lado == "visitante":
        evento.goles_visitante += 1
        equipo_gol = evento.equipo_visitante
    else:
        raise ErrorApuesta("Lado inválido: usa local o visitante.")

    evento.status = EstadoEvento.EN_VIVO
    evento.save(update_fields=["goles_local", "goles_visitante", "status"])
    cuotas_actualizadas = recalcular_cuotas_inplay(evento)

    mercados = Mercado.objects.filter(evento=evento, tipo=TipoMercado.RESULTADO_1X2)
    for mercado in mercados:
        suspender_mercado_por_evento_critico(mercado.id, segundos=segundos)

    broadcast_odds_evento(
        evento.id,
        {
            "tipo": "gol",
            "evento_id": evento.id,
            "lado": lado,
            "equipo_gol": equipo_gol,
            "goles_local": evento.goles_local,
            "goles_visitante": evento.goles_visitante,
            "marcador": evento.marcador,
            "segundos_suspension": segundos or settings.MERCADO_SUSPENSION_SEGUNDOS,
            "cuotas_actualizadas": len(cuotas_actualizadas),
        },
    )
    return evento


@transaction.atomic
def liquidar_apuesta(apuesta: Apuesta, evento: EventoDeportivo) -> Apuesta:
    if apuesta.status != EstadoApuesta.ACEPTADA:
        return apuesta

    if evento.status == EstadoEvento.ANULADO:
        servicios_wallet.reembolsar_apuesta_anulada(
            apuesta.user,
            apuesta.stake,
            str(apuesta.id),
            idempotency_key=f"settle-void-{apuesta.id}",
        )
        apuesta.status = EstadoApuesta.ANULADA
        apuesta.save(update_fields=["status"])
        return apuesta

    resultado = _seleccion_es_ganadora(apuesta.seleccion, evento)
    if resultado is None:
        return apuesta

    if resultado:
        payout = apuesta.payout_potencial
        servicios_wallet.liquidar_apuesta_ganada(
            apuesta.user,
            apuesta.stake,
            payout,
            str(apuesta.id),
            idempotency_key=f"settle-win-{apuesta.id}",
        )
        apuesta.status = EstadoApuesta.GANADA
    else:
        servicios_wallet.liquidar_apuesta_perdida(
            apuesta.user,
            apuesta.stake,
            str(apuesta.id),
            idempotency_key=f"settle-loss-{apuesta.id}",
        )
        apuesta.status = EstadoApuesta.PERDIDA

    apuesta.save(update_fields=["status"])
    return apuesta


@transaction.atomic
def liquidar_combinada(combinada: ApuestaCombinada) -> ApuestaCombinada:
    if combinada.status != EstadoApuesta.ACEPTADA:
        return combinada

    piernas = list(
        combinada.piernas.select_related("evento", "seleccion", "seleccion__mercado")
    )
    for pierna in piernas:
        if pierna.evento.status not in (EstadoEvento.FINALIZADO, EstadoEvento.ANULADO):
            return combinada

    pierna_perdida = False
    pendiente = False
    for pierna in piernas:
        ev = pierna.evento
        if ev.status == EstadoEvento.ANULADO:
            combinada.status = EstadoApuesta.ANULADA
            servicios_wallet.reembolsar_apuesta_anulada(
                combinada.user,
                combinada.stake,
                str(combinada.id),
                idempotency_key=f"combo-void-{combinada.id}",
            )
            combinada.save(update_fields=["status"])
            return combinada
        resultado = _pierna_combinada_ganadora(pierna)
        if resultado is None:
            pendiente = True
            break
        if not resultado:
            pierna_perdida = True
            break

    if pendiente:
        return combinada

    if pierna_perdida:
        servicios_wallet.liquidar_apuesta_perdida(
            combinada.user,
            combinada.stake,
            str(combinada.id),
            idempotency_key=f"combo-loss-{combinada.id}",
        )
        combinada.status = EstadoApuesta.PERDIDA
    else:
        payout = combinada.payout_potencial
        servicios_wallet.liquidar_apuesta_ganada(
            combinada.user,
            combinada.stake,
            payout,
            str(combinada.id),
            idempotency_key=f"combo-win-{combinada.id}",
        )
        combinada.status = EstadoApuesta.GANADA

    combinada.save(update_fields=["status"])
    return combinada


def liquidar_combinadas_afectadas_por_evento(evento_id: int) -> int:
    count = 0
    combinadas_ids = (
        PiernaCombinada.objects.filter(evento_id=evento_id)
        .values_list("combinada_id", flat=True)
        .distinct()
    )
    for comb in ApuestaCombinada.objects.filter(pk__in=combinadas_ids, status=EstadoApuesta.ACEPTADA):
        liquidar_combinada(comb)
        count += 1
    return count


@transaction.atomic
def liquidar_evento(evento: EventoDeportivo) -> dict:
    evento = EventoDeportivo.objects.select_for_update().get(pk=evento.pk)

    if evento.status not in (EstadoEvento.FINALIZADO, EstadoEvento.ANULADO):
        raise ErrorApuesta(
            "El evento debe estar en estado finalizado o anulado para liquidar."
        )

    if evento.status == EstadoEvento.FINALIZADO and not evento.seleccion_ganadora_id:
        hay_1x2 = Apuesta.objects.filter(
            evento=evento,
            status=EstadoApuesta.ACEPTADA,
            seleccion__mercado__tipo=TipoMercado.RESULTADO_1X2,
        ).exists() or PiernaCombinada.objects.filter(
            evento=evento,
            combinada__status=EstadoApuesta.ACEPTADA,
            seleccion__mercado__tipo=TipoMercado.RESULTADO_1X2,
        ).exists()
        if hay_1x2:
            raise ErrorApuesta("Define la selección ganadora 1X2 antes de liquidar.")

    pendientes = mercados_sin_ganador_para_liquidacion(evento)
    if pendientes:
        nombres = ", ".join(m.nombre for m in pendientes)
        raise ErrorApuesta(
            f"Faltan ganadores en mercados: {nombres}. "
            "Márcalos en Admin → Mercados antes de liquidar."
        )

    contadores = {"ganadas": 0, "perdidas": 0, "anuladas": 0, "combinadas": 0}
    apuestas = Apuesta.objects.filter(evento=evento, status=EstadoApuesta.ACEPTADA).select_related(
        "user", "seleccion"
    )

    for apuesta in apuestas:
        antes = apuesta.status
        liquidar_apuesta(apuesta, evento)
        apuesta.refresh_from_db()
        if apuesta.status == EstadoApuesta.GANADA and antes != EstadoApuesta.GANADA:
            contadores["ganadas"] += 1
        elif apuesta.status == EstadoApuesta.PERDIDA:
            contadores["perdidas"] += 1
        elif apuesta.status == EstadoApuesta.ANULADA:
            contadores["anuladas"] += 1

    contadores["combinadas"] = liquidar_combinadas_afectadas_por_evento(evento.id)
    return contadores
