# Avance del proyecto (~40 %)

**Proyecto:** FairBet Lab — simulador educativo de apuestas  
**Fecha del avance:** mayo 2026  

---

## Resumen para el profesor (30 segundos)

Montamos el **entorno Docker** (Django, PostgreSQL, Redis, Celery, Channels) y avanzamos el **Nivel 1 parcial** del challenge:

| Hecho en este avance | % aprox. del Nivel 1 |
|----------------------|----------------------|
| Registro + validación DNI + edad + estados KYC | ~80 % |
| Wallet partida doble + recarga simulada + bloqueo por apuesta | ~70 % |
| Catálogo eventos 1X2 + seed demo | ~60 % |
| Apuesta simple (colocar, sin liquidar aún) | ~50 % |
| Juego responsable (límite diario recarga + mensaje en apuesta) | ~30 % |
| Tests wallet (invariantes básicas) | ~40 % |

**No incluido aún (siguiente fase):** liquidación de apuestas, retiro simulado, autoexclusión completa, Channels en vivo, auditoría hash, 80 % cobertura, ADRs completos, combinadas, cash-out, etc.

---

## Cómo probar rápido

Ver guía detallada: **`docs/guias/04-COMO-PROBAR-EL-AVANCE.md`**

```powershell
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

---

## Mapa de guías de estudio

| Archivo | Qué explica |
|---------|-------------|
| `docs/guias/00-INDICE.md` | Índice de todas las guías |
| `docs/guias/01-PASO-USUARIOS-KYC.md` | App `users`, DNI, registro |
| `docs/guias/02-PASO-WALLET.md` | Partida doble, LedgerEntry |
| `docs/guias/03-PASO-EVENTOS-APUESTAS.md` | Eventos, mercado 1X2, apuestas |
| `docs/guias/04-COMO-PROBAR-EL-AVANCE.md` | Pasos con Postman o navegador |
| `docs/guias/05-QUE-FALTA-PARA-TERMINAR.md` | Roadmap al 100 % |
| `docs/guias/06-PANEL-ADMIN-DJANGO.md` | Explicación del panel `/admin/` |
| `docs/GUIA_ENTORNO_Y_PROYECTO.md` | Docker y servicios |

---

## Endpoints disponibles en este avance

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/users/register/` | Registro |
| POST | `/api/users/verify-kyc/` | Simular verificación (demo) |
| GET | `/api/users/me/` | Mi perfil |
| GET | `/api/wallet/balance/` | Saldo calculado |
| POST | `/api/wallet/deposit/` | Recarga fichas |
| GET | `/api/events/` | Listar partidos |
| POST | `/api/bets/` | Apostar |
| GET | `/api/bets/mine/` | Mis apuestas |

Autenticación: header `Authorization: Token <token>` después del registro.
