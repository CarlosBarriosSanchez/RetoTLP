# Guía 03 — Eventos, mercados y apuestas simples

## ¿Qué problema resuelve?

El usuario debe ver **partidos disponibles**, elegir un resultado (1X2) con una **cuota** (odds) y apostar una cantidad de fichas.

---

## Modelos (tablas en PostgreSQL)

```
SportEvent (partido)
    └── Market (ej. "Resultado 1X2")
            └── MarketSelection (Local / Empate / Visitante + odds)
```

| Modelo | Ejemplo de dato |
|--------|-----------------|
| `SportEvent` | Perú vs Chile, status `programado` |
| `Market` | tipo `1X2` |
| `MarketSelection` | "Gana Perú", codigo `1`, odds `2.10` |
| `Bet` | usuario apostó 10 fichas a cuota 2.10, status `accepted` |

---

## Archivos

| Archivo | Sirve para |
|---------|------------|
| `apps/betting/models.py` | Estructura de datos |
| `apps/betting/services.py` | Reglas al apostar + llama al wallet |
| `apps/betting/views.py` | API listar eventos, apostar, mis apuestas |
| `apps/betting/serializers.py` | Formato JSON de respuesta |
| `apps/betting/management/commands/seed_demo.py` | Crea 3 partidos de prueba |

---

## Flujo al apostar (lo más importante)

```
POST /api/bets/
     ↓
views.PlaceBetView
     ↓
services.colocar_apuesta_simple()
     ├─ ¿Cuenta verificada?
     ├─ ¿Evento programado?
     ├─ ¿Monto entre 1 y 500?
     └─ wallet.bloquear_fondos_apuesta()  ← partida doble
     ↓
Bet guardada en status accepted
```

**Payout potencial** = `stake × odds` (solo informativo hasta liquidar).

---

## Estados del evento

| Status | ¿Se puede apostar en este avance? |
|--------|-----------------------------------|
| `programado` | Sí |
| `en_vivo` | No (fase 2) |
| `finalizado` | No |

---

## Conexión con wallet

La apuesta **no resta saldo mágicamente**: llama a `bloquear_fondos_apuesta`, que escribe en `LedgerEntry`. Por eso wallet y betting van ligados.

---

## Juego responsable en este avance

- Mensaje obligatorio en la respuesta de `POST /api/bets/`.  
- Límite diario de recarga en `UserProfile.limite_deposito_diario` (wallet).

Falta: límites semanal/mensual, autoexclusión, cooldown al subir límites.

---

## Frase para el profesor

> *"Separamos catálogo (eventos/mercados) de la ejecución de la apuesta. Al confirmar, bloqueamos fichas vía ledger antes de dejar la Bet en accepted; la liquidación cuando termina el partido es trabajo pendiente."*

---

## Qué falta

- Liquidación automática al marcar resultado  
- Máquina de estados completa (won, lost, void)  
- Apuestas combinadas, in-play, cash-out  
- Channels para cambio de cuotas en vivo  
