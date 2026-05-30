# Guía 04 — Cómo probar el avance (~40 %)

## Antes de empezar

1. Docker Desktop encendido.  
2. En la carpeta del proyecto:

```powershell
cd C:\Users\JORDAN\Documents\TALLER_LENGUAJE
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

3. Abre en el navegador: http://localhost:8000/ (página inicio con footer legal)

---

## Paso 1 — Registrar usuario

**POST** `http://localhost:8000/api/users/register/`

Cuerpo JSON (ejemplo con DNI válido):

```json
{
  "username": "jordan",
  "email": "jordan@test.com",
  "password": "jordan1011",
  "dni": "77814916",
  "fecha_nacimiento": "2000-11-10"
}
```

**Respuesta:** guarda el `"token"` que te devuelve.

> El DNI debe ser **8 números** sin puntos ni guiones (tu `77814916` es válido).

---

## Paso 2 — Verificar KYC (simulación)

Header: `Authorization: Token TU_TOKEN_AQUI`

**POST** `http://localhost:8000/api/users/verify-kyc/`

Sin cuerpo. Debe cambiar `status` a `verificado`.

---

## Paso 3 — Recargar fichas

**POST** `http://localhost:8000/api/wallet/deposit/`

```json
{
  "monto": "100.0000",
  "idempotency_key": "recarga-001"
}
```

**GET** `http://localhost:8000/api/wallet/balance/` → debe mostrar `100.0000`.

---

## Paso 4 — Ver partidos

**GET** `http://localhost:8000/api/events/`  
(No requiere token.)

Anota `id` del evento y `id` de una selección (ej. "Gana Perú").

---

## Paso 5 — Apostar

**POST** `http://localhost:8000/api/bets/`

```json
{
  "event_id": 1,
  "selection_id": 1,
  "stake": "25.0000",
  "idempotency_key": "apuesta-001"
}
```

Debe incluir mensaje de **juego responsable** y `payout_potencial`.

**GET** `http://localhost:8000/api/bets/mine/` — lista tus apuestas.

**GET** balance otra vez → saldo debe ser `75.0000` si recargaste 100 y apostaste 25.

---

## Paso 6 — Panel admin (opcional)

```powershell
docker compose exec web python manage.py createsuperuser
```

http://localhost:8000/admin/ → ver usuarios, movimientos ledger, apuestas.

**¿Qué significa cada menú del admin?** Lee **`06-PANEL-ADMIN-DJANGO.md`**.

---

## Probar tests automáticos

```powershell
docker compose exec web pytest apps/wallet/tests/ -v
```

4 tests deben pasar (saldo, partida doble, idempotencia, bloqueo).

---

## Si algo falla

| Error | Qué revisar |
|-------|-------------|
| 401 Unauthorized | ¿Pusiste el header Token? |
| Cuenta no verificada | ¿Hiciste verify-kyc? |
| Saldo insuficiente | ¿Depositaste antes de apostar? |
| DNI inválido | Último dígito del DNI |

---

## Herramientas

- Navegador en rutas GET  
- Extensión REST Client de VS Code  
- Postman / Insomnia  
