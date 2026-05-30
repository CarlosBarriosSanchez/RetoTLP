# Guía 02 — Wallet y partida doble

## ¿Qué problema resuelve?

Las **fichas virtuales** del usuario deben moverse sin errores: si recargas 100 y apuestas 40, el saldo debe ser 60 siempre, aunque dos personas apuesten al mismo tiempo.

El enunciado exige **partida doble**: cada movimiento tiene al menos un **débito** y un **crédito** que se anulan (suma cero).

---

## Idea simple de partida doble

Imagina un cuaderno donde **nunca guardas el saldo en una celda fija**, solo anotas movimientos:

| Cuenta | Dirección | Monto | Significado |
|--------|-----------|-------|-------------|
| wallet_usuario | CREDIT | 100 | Entran fichas al usuario |
| casa | DEBIT | 100 | La casa "soltó" esas fichas |

**Saldo del usuario** = suma de CREDIT − suma de DEBIT en `wallet_usuario`.

---

## Archivos y conexiones

| Archivo | Sirve para |
|---------|------------|
| `apps/wallet/models.py` | `LedgerTransaction` (grupo) y `LedgerEntry` (línea) |
| `apps/wallet/services.py` | **Cerebro:** recarga, bloqueo apuesta, calcular saldo |
| `apps/wallet/views.py` | API balance y deposit |
| `apps/wallet/tests/test_services.py` | Pruebas: saldo, balance, idempotencia |

```
API /api/wallet/deposit/
        ↓
views.py → services.recarga_simulada()
        ↓
PostgreSQL: 2 LedgerEntry en una transacción atómica
        ↓
calcular_saldo() lee SUM() — no hay columna "saldo"
```

---

## Cuentas que usamos (avance)

| Cuenta | Uso |
|--------|-----|
| `wallet_usuario` | Fichas disponibles del jugador |
| `casa` | Contrapartida del operador |
| `apuestas_pendientes` | Fichas bloqueadas al apostar |
| `bonos` | Reservada para promos (aún vacía) |

---

## Operaciones implementadas

### 1. Recarga simulada (`deposito_simulado`)

- CREDIT `wallet_usuario`  
- DEBIT `casa`  
- Revisa: cuenta verificada, no autoexcluida, **límite diario** (juego responsable básico).

### 2. Bloqueo por apuesta (`bloqueo_apuesta`)

- DEBIT `wallet_usuario`  
- CREDIT `apuestas_pendientes`  
- Usa `select_for_update()` para evitar doble gasto concurrente.

---

## ¿Por qué Decimal y no float?

`float` redondea mal (0.1 + 0.2 ≠ 0.3). Con dinero simulado usamos `Decimal` con 4 decimales en `settings.py`.

---

## Idempotencia

Si envías la misma `idempotency_key` dos veces, **no se duplica** el movimiento. Importante cuando la red falla y el cliente reintenta.

---

## Frase para el profesor

> *"El saldo es una vista calculada sobre el libro mayor. Cada operación financiera es una transacción balanceada; los tests verifican que débitos igualan créditos y que la idempotencia no duplica depósitos."*

---

## Qué falta (siguiente fase)

- Retiro simulado  
- Liquidación ganadora/perdedora (mover de `apuestas_pendientes` a casa o wallet)  
- Tests Hypothesis y concurrencia N peticiones  
- 80 % cobertura formal  
