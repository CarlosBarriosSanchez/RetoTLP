# Guía 05 — Qué falta para terminar el challenge

Comparado con `index.html` (enunciado completo).

## Ya hecho (~40 % global)

- [x] Entorno Docker completo  
- [x] Registro + DNI + edad + estados KYC básicos  
- [x] Wallet partida doble (recarga + bloqueo apuesta)  
- [x] Saldo calculado, Decimal, idempotencia depósito  
- [x] Eventos + mercado 1X2 + seed  
- [x] Apuesta simple hasta `accepted`  
- [x] Límite diario recarga + mensaje juego responsable en apuesta  
- [x] Tests wallet básicos  
- [x] Guías de estudio  

## Nivel 1 pendiente (para llegar al 55 % obligatorio)

- [ ] Retiro simulado de fichas  
- [ ] Liquidación de apuestas (won/lost) con payout exacto  
- [ ] Admin/sistema marca resultado del evento  
- [ ] Autoexclusión 7/30/90 días bloqueante  
- [ ] Límites semanal y mensual + cooldown 24h al subir límite  
- [ ] Mensaje responsable en **todas** las pantallas (frontend real)  

## Nivel 2 (25 %)

- [ ] Apuestas combinadas  
- [ ] Django Channels cuotas en vivo  
- [ ] In-play y suspensión de mercado  
- [ ] Cash-out  
- [ ] Mercados Over/Under, BTTS, handicap  

## Nivel 3 (20 %)

- [ ] Auditoría hash encadenado (`apps/audit`)  
- [ ] Anti-fraude y alertas  
- [ ] Dashboard operador GGR  
- [ ] Reporte CSV MINCETUR  

## Entregables de proceso

- [ ] 10+ ADRs en `docs/adr/`  
- [ ] Bocetos en `docs/sketches/`  
- [ ] Conventional Commits + TDD visible  
- [ ] `docs/lecciones.md`, `docs/anti-ai-disclosure.md`  
- [ ] Video demo 7–10 min  
- [ ] Cobertura 80 % wallet + betting  
- [ ] Tests Hypothesis y concurrencia  

## Orden sugerido para el siguiente sprint

1. Liquidación de apuestas + máquina de estados Bet  
2. Autoexclusión y límites completos  
3. Más tests (Hypothesis + concurrencia)  
4. Frontend mínimo o OpenAPI documentada  
5. Auditoría y dashboard  
