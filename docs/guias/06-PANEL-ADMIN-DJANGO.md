# Guía 06 — Panel de administración Django (`/admin/`)

## ¿Qué es este panel?

Es la **consola del operador** de tu proyecto: una interfaz web que Django trae incluida para **ver y editar datos** en la base de datos (PostgreSQL) sin usar Postman.

| Postman | Admin |
|---------|--------|
| Lo usa el **usuario/jugador** (API) | Lo usa el **administrador** del sistema |
| Registro, apostar, recargar | Ver todo, corregir, verificar KYC, crear eventos |
| JSON y headers | Formularios y tablas |

**URL:** http://localhost:8000/admin/  
**Login:** el usuario que creaste con `createsuperuser` (no es el mismo token de Postman).

---

## Vista general de las secciones (como en tu captura)

```
Administración de Django
├── AUTENTICACIÓN Y AUTORIZACIÓN     ← Django (sistema)
├── EVENTOS, MERCADOS Y APUESTAS     ← Tu app betting (avance)
├── TAREAS PERIÓDICAS                ← Celery Beat (futuro)
├── TOKEN DE AUTENTICACIÓN           ← Tokens de Postman
├── USUARIOS Y KYC                   ← Tu app users
└── WALLET (PARTIDA DOBLE)           ← Tu app wallet
```

Algunas listas están **vacías** porque aún no las usaste o porque esa función se programará después.

---

# 1. AUTENTICACIÓN Y AUTORIZACIÓN

Viene de **Django**, no la creamos nosotros. Controla **quién puede entrar al admin** y qué permisos tiene.

## Grupos

| | |
|--|--|
| **¿Para qué sirve?** | Agrupar permisos (ej. “operadores”, “soporte”) y asignarlos a varios usuarios a la vez. |
| **¿Lo usamos en el avance?** | Casi no. Por defecto está vacío (0 grupos). |
| **¿Por qué está vacío?** | No configuramos roles todavía; solo tu superusuario entra al admin. |
| **¿Para el challenge?** | Útil cuando haya equipo con distintos roles (admin vs operador de apuestas). |

**Ejemplo futuro:** grupo “Operador” puede ver apuestas pero no borrar usuarios.

---

## Usuarios

| | |
|--|--|
| **¿Para qué sirve?** | Cuentas de **login** del sistema: username, email, contraseña, si es staff/superuser. |
| **¿Lo usamos?** | **Sí.** Aquí aparece tu usuario de `createsuperuser` y los que se registran por API (`/api/users/register/`). |
| **Tabla en BD** | `auth_user` |
| **Conexión** | Cada registro en Postman crea un `User`. Luego se enlaza a **Perfil de usuario** (KYC). |

**Qué puedes hacer aquí:**
- Ver quién se registró.
- Marcar `Staff status` / `Superuser` (dar acceso al admin).
- Desactivar cuenta (`Active` = no).
- **No** edita DNI ni estado KYC directamente (eso está en *Perfiles de usuario*).

**Diferencia importante:**

| Usuarios (auth) | Perfiles de usuario (KYC) |
|-----------------|---------------------------|
| Login y contraseña | DNI, edad, estado verificado |
| Token de Postman ligado a esto | Reglas para apostar/recargar |

---

# 2. EVENTOS, MERCADOS Y APUESTAS

Viene de la app **`apps/betting`**. Es el corazón del catálogo deportivo y las apuestas.

## Sport events (Eventos deportivos)

| | |
|--|--|
| **¿Para qué sirve?** | Partidos: Perú vs Chile, fecha, estado (`programado`, `en_vivo`, `finalizado`, etc.). |
| **¿Lo usamos?** | **Sí**, si corriste `python manage.py seed_demo` verás 3 partidos. |
| **¿Qué ves al entrar?** | Lista de partidos; al abrir uno, abajo aparecen **mercados** (inline). |

**Estados del evento (para explicar al profesor):**

| Estado | Significado | ¿Apostar en avance actual? |
|--------|-------------|----------------------------|
| `programado` | Aún no empieza | Sí |
| `en_vivo` | En curso | No (fase 2) |
| `finalizado` | Terminó | No |
| `suspendido` / `anulado` | Pausado o cancelado | No |

**Desde el admin puedes:** crear partidos manualmente, cambiar estado, poner fecha de inicio.

---

## Mercados y selecciones (dentro del evento, no menú aparte)

No aparecen como menú principal porque están **dentro** del formulario de *Sport event*:

| Modelo | ¿Qué es? | Ejemplo |
|--------|----------|---------|
| **Market** | Tipo de apuesta del partido | “Resultado 1X2” |
| **MarketSelection** | Opción + cuota | “Gana Perú” @ 2.10 |

**¿Por qué no hay menú “Mercados”?**  
Solo registramos `SportEvent` y `Bet` en el admin; mercados se editan **inline** al abrir un evento.

**Si ves eventos pero “sin mercados”:** abre el evento → pestaña inferior → añade mercado 1X2 y 3 selecciones (1, X, 2).

---

## Bets (Apuestas)

| | |
|--|--|
| **¿Para qué sirve?** | Cada apuesta que un usuario hizo: monto, cuota bloqueada, estado, enlace al evento. |
| **¿Lo usamos?** | **Sí**, después de apostar por Postman (`POST /api/bets/`). |
| **Estado actual** | Casi siempre `accepted` (avance ~40 %). |
| **Falta implementar** | `won`, `lost`, liquidación automática al cerrar el partido. |

**Qué muestra cada campo útil:**

| Campo | Significado |
|-------|-------------|
| `user` | Quién apostó |
| `stake` | Fichas apostadas |
| `odds_locked` | Cuota al momento de apostar |
| `ledger_transaction` | Movimiento contable que bloqueó las fichas |
| `status` | Estado de la apuesta |

**Desde el admin puedes:** auditar apuestas, buscar por usuario, ver historial (demo / soporte).

---

# 3. TAREAS PERIÓDICAS

Viene de **`django-celery-beat`** (Celery + Redis en Docker). Sirve para **programar tareas automáticas** en el servidor.

| Opción | ¿Para qué sirve? | ¿Lo usamos ahora? |
|--------|------------------|-------------------|
| **Tareas periódicas** | Lista de trabajos programados (nombre + función + horario) | No configuradas |
| **Intervalos** | “Cada X minutos/horas” | Vacío |
| **Crontabs** | “Todos los días a las 8:00” (estilo cron) | Vacío |
| **Cronometrado** | Ejecutar **una vez** en fecha/hora exacta | Vacío |
| **Eventos solares** | Horarios según amanecer/atardecer (raro en apuestas) | Vacío |

**¿Por qué todo vacío?**  
El contenedor `celery-beat` ya corre, pero **aún no definimos tareas** del negocio.

**Ejemplos para el challenge (futuro):**

- Cada minuto: revisar eventos que pasan a `en_vivo`.
- Al finalizar partido: liquidar apuestas automáticamente.
- Cada noche: reporte CSV para MINCETUR.

**Frase para el profesor:**  
*“La infraestructura de tareas programadas está lista con Celery Beat; las tareas de negocio se agregarán en la siguiente iteración.”*

---

# 4. TOKEN DE AUTENTICACIÓN

Viene de **`rest_framework.authtoken`**. Guarda el **token** que usas en Postman.

| | |
|--|--|
| **¿Para qué sirve?** | Cada fila = un token largo ligado a un `User`. Header: `Authorization: Token xxxxx` |
| **¿Lo usamos?** | **Sí.** Al registrarte (`/api/users/register/`) se crea uno automáticamente. |
| **¿Qué ves?** | Usuario + clave del token (puedes revocar borrando la fila). |

**No confundir:**

| Admin login | API Token |
|-------------|-----------|
| Usuario + contraseña en `/admin/` | `Token ...` en Postman |
| Sesión de navegador | Autenticación de la API |

**Seguridad:** en producción no se muestran tokens en pantalla al usuario; el admin solo es para desarrollo/demo.

---

# 5. USUARIOS Y KYC

Viene de **`apps/users`**.

## Perfiles de usuario

| | |
|--|--|
| **¿Para qué sirve?** | Datos del **KYC simulado**: DNI, fecha de nacimiento, `status`, límite diario de recarga. |
| **¿Lo usamos?** | **Sí.** Un perfil por cada usuario registrado por API. |
| **Tabla** | `users_userprofile` |

**Estados (`status`):**

| Valor | ¿Puede recargar/apostar? |
|-------|--------------------------|
| `pendiente_verificacion` | No |
| `verificado` | Sí |
| `bloqueado` | No |
| `autoexcluido` | No (juego responsable, futuro completo) |

**En Postman** verificas con `POST /api/users/verify-kyc/`.  
**En admin** puedes cambiar el estado manualmente (útil para demo: poner `verificado` sin Postman).

**Campos importantes:**

| Campo | Uso |
|-------|-----|
| `dni` | Documento peruano (8 dígitos) |
| `limite_deposito_diario` | Juego responsable: tope de recarga por día |
| `autoexclusion_hasta` | Reservado para autoexclusión (aún básico) |

---

# 6. WALLET (PARTIDA DOBLE)

Viene de **`apps/wallet`**. Aquí ves la **contabilidad** de fichas virtuales.

## Ledger transactions (Transacciones del libro)

| | |
|--|--|
| **¿Para qué sirve?** | Cada **operación financiera** agrupada: recarga, bloqueo de apuesta, etc. |
| **¿Lo usamos?** | **Sí**, al recargar (`deposit`) o apostar (`bloqueo_apuesta`). |
| **Al abrir una fila** | Ves las **líneas** (Ledger entry) abajo: débitos y créditos. |

**Tipos que verás en el avance:**

| `tipo` | Cuándo ocurre |
|--------|----------------|
| `deposito_simulado` | Recarga de fichas |
| `bloqueo_apuesta` | Usuario apostó; fichas van a “pendientes” |

**Falta en el futuro:** liquidación ganadora/perdedora, retiro simulado, bonos.

---

## Ledger entry (líneas — dentro de la transacción)

No tiene menú propio; aparece **inline** dentro de cada transacción.

| Campo | Significado |
|-------|-------------|
| `account` | `wallet_usuario`, `casa`, `apuestas_pendientes`, `bonos` |
| `direction` | `DEBIT` (resta de esa cuenta) o `CREDIT` (suma) |
| `amount` | Cantidad de fichas (Decimal, no float) |
| `user` | A quién aplica (puede ser null en cuenta `casa`) |

**Regla de oro (partida doble):**  
En cada transacción, **suma de débitos = suma de créditos**. El saldo del jugador **no** está en una columna; se **calcula** desde estas líneas.

**Ejemplo recarga 100:**

| Cuenta | Dirección | Monto |
|--------|-----------|-------|
| wallet_usuario | CREDIT | 100 |
| casa | DEBIT | 100 |

---

# 7. Cosas que NO ves en el admin (pero existen en el código)

| Qué | Por qué no aparece |
|-----|-------------------|
| **Auditoría inmutable** (`apps/audit`) | Aún no implementada (Nivel 3 del enunciado) |
| **Mercados / selecciones** como menú | Solo editables dentro de cada evento |
| **Ledger entry** como menú | Solo dentro de cada transacción |
| **Anti-fraude, dashboard GGR** | Pendiente Nivel 3 |

---

# 8. ¿Qué debería tener datos hoy si probaste Postman?

| Sección | ¿Debería tener datos? |
|---------|------------------------|
| Usuarios | Sí (tú + registros API) |
| Perfiles de usuario | Sí (DNI, status) |
| Tokens | Sí (uno por usuario API) |
| Sport events | Sí (si corriste `seed_demo`) |
| Bets | Sí (si apostaste) |
| Ledger transactions | Sí (si recargaste o apostaste) |
| Grupos | No (normal) |
| Tareas periódicas | No (normal) |

---

# 9. Flujo mental: Postman + Admin

```
Usuario en Postman                    Admin (tú como operador)
─────────────────────                 ─────────────────────────
register  ──────────►  User + Profile + Token
verify-kyc ─────────►  status = verificado (también editable en admin)
deposit   ──────────►  LedgerTransaction + 2 entries
GET events ◄────────  Sport events (creados por seed o admin)
POST bet  ──────────►  Bet + bloqueo en ledger
                      Todo visible en admin para auditar
```

---

# 10. Guion corto para explicar al profesor

> *“El panel `/admin/` es la vista del operador sobre PostgreSQL. Ahí vemos usuarios y perfiles KYC, tokens de API, eventos y apuestas, y el libro mayor con partida doble. Las tareas periódicas de Celery Beat están instaladas pero sin jobs de negocio aún. Lo que está vacío corresponde a funciones futuras del challenge o a roles que no configuramos en este avance del 40 %.”*

---

# 11. Comandos útiles relacionados

```powershell
# Crear admin
docker compose exec web python manage.py createsuperuser

# Datos de demo (partidos)
docker compose exec web python manage.py seed_demo
```

---

**Siguiente lectura:** `04-COMO-PROBAR-EL-AVANCE.md` (flujo Postman) · `05-QUE-FALTA-PARA-TERMINAR.md` (roadmap)
