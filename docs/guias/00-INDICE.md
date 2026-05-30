# Índice de guías — FairBet Lab

Estas guías están pensadas para que **entiendas y expliques** el proyecto sin ser experto en Docker o Django.

## Orden de lectura recomendado

1. **`../GUIA_ENTORNO_Y_PROYECTO.md`** — Qué es Docker, PostgreSQL, Redis, etc.
2. **`../AVANCE_40_PORCIENTO.md`** — Qué está hecho y qué falta (~40 %)
3. **`01-PASO-USUARIOS-KYC.md`** — Registro y verificación simulada
4. **`02-PASO-WALLET.md`** — Fichas virtuales y partida doble
5. **`03-PASO-EVENTOS-APUESTAS.md`** — Partidos, cuotas y apostar
6. **`04-COMO-PROBAR-EL-AVANCE.md`** — Prueba manual paso a paso
7. **`05-QUE-FALTA-PARA-TERMINAR.md`** — Próximos pasos del challenge
8. **`06-PANEL-ADMIN-DJANGO.md`** — Qué es cada opción del `/admin/`
9. **`07-DEFENSA-ORAL-Y-PREGUNTAS-PROFESOR.md`** — Decoradores, preguntas del profesor, compartir con el equipo

## Idea general del flujo

```
Usuario se registra (users)
       ↓
Verifica KYC simulado (users)
       ↓
Recarga fichas (wallet) ← PostgreSQL guarda cada movimiento
       ↓
Ve partidos (betting)
       ↓
Apuesta → se bloquean fichas (wallet + betting)
```

Cada guía explica **qué archivo hace qué** y **con qué se conecta**.
