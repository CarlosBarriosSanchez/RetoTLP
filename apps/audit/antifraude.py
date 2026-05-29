from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from apps.audit.context import get_client_ip
from apps.audit.models import ActividadSospechosa, RegistroAuditoria, SeveridadAlerta, TipoAlerta
from apps.betting.models import Apuesta, EstadoApuesta
from apps.wallet.models import TransaccionContable

User = get_user_model()


def _crear_alerta(tipo, descripcion, usuario=None, severidad=SeveridadAlerta.MEDIA, metadata=None):
    ip = get_client_ip()
    if ActividadSospechosa.objects.filter(
        tipo=tipo,
        usuario=usuario,
        descripcion=descripcion,
        resuelta=False,
        creado_en__gte=timezone.now() - timedelta(hours=24),
    ).exists():
        return None
    return ActividadSospechosa.objects.create(
        tipo=tipo,
        severidad=severidad,
        descripcion=descripcion,
        usuario=usuario,
        ip_origen=ip,
        metadata=metadata or {},
    )


def evaluar_registro_usuario(user) -> None:
    ip = get_client_ip()
    if not ip:
        return
    desde = timezone.now() - timedelta(days=1)
    usuarios_ip = (
        RegistroAuditoria.objects.filter(
            tipo_evento="registro_usuario",
            ip_origen=ip,
            creado_en__gte=desde,
        )
        .values("usuario")
        .distinct()
        .count()
    )
    if usuarios_ip >= 3:
        _crear_alerta(
            TipoAlerta.MULTIPLES_CUENTAS_IP,
            f"IP {ip} registró {usuarios_ip} cuentas en 24 h.",
            usuario=user,
            severidad=SeveridadAlerta.ALTA,
            metadata={"ip": ip, "cuentas": usuarios_ip},
        )


def evaluar_deposito_seguido_cashout(user) -> None:
    ip = get_client_ip()
    hace = timezone.now() - timedelta(hours=2)
    deposito_reciente = TransaccionContable.objects.filter(
        tipo="deposito_simulado",
        referencia=f"user:{user.id}",
        creado_en__gte=hace,
    ).exists()
    if not deposito_reciente:
        return
    cashout_reciente = Apuesta.objects.filter(
        user=user,
        status=EstadoApuesta.CASHOUT,
        cashout_en__gte=hace,
    ).exists()
    if cashout_reciente:
        _crear_alerta(
            TipoAlerta.DEPOSITO_CASHOUT_RAPIDO,
            f"Usuario {user.username}: recarga y cash-out en menos de 2 h.",
            usuario=user,
            severidad=SeveridadAlerta.MEDIA,
            metadata={"ip": ip},
        )


def evaluar_apuestas_espejo(apuesta: Apuesta) -> None:
    """Varios usuarios apuestan lo mismo (evento+selección+stake) en pocos minutos."""
    ventana = timezone.now() - timedelta(minutes=10)
    coincidencias = (
        Apuesta.objects.filter(
            evento=apuesta.evento,
            seleccion=apuesta.seleccion,
            stake=apuesta.stake,
            creado_en__gte=ventana,
        )
        .values("user")
        .distinct()
        .count()
    )
    if coincidencias >= 3:
        _crear_alerta(
            TipoAlerta.APUESTAS_ESPEJO,
            f"Patrón espejo en {apuesta.evento}: {coincidencias} usuarios, "
            f"mismo stake {apuesta.stake} y selección {apuesta.seleccion.etiqueta}.",
            usuario=apuesta.user,
            severidad=SeveridadAlerta.BAJA,
            metadata={"evento_id": apuesta.evento_id, "coincidencias": coincidencias},
        )


def evaluar_intentos_abuso_bono(user) -> None:
    """
    Marca alerta cuando hay varios intentos de retiro bloqueados por rollover
    en una ventana corta, señal de intento de extraer bono sin apostar.
    """
    ip = get_client_ip()
    ventana = timezone.now() - timedelta(hours=24)
    intentos = RegistroAuditoria.objects.filter(
        tipo_evento="retiro_bloqueado_rollover",
        usuario=user,
        creado_en__gte=ventana,
    ).count()
    if intentos >= 3:
        _crear_alerta(
            TipoAlerta.ABUSO_BONO,
            f"Usuario {user.username}: {intentos} retiros bloqueados por rollover en 24 h.",
            usuario=user,
            severidad=SeveridadAlerta.MEDIA,
            metadata={"ip": ip, "intentos": intentos},
        )
