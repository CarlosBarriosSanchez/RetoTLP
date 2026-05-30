# Mapa de páginas del frontend

Rutas web definidas en `config/urls.py`. Cada página extiende `templates/base.html`.

## Páginas públicas

| Ruta | Template | Descripción |
|------|----------|-------------|
| `/` | `home.html` | Landing: qué es el simulador y enlaces rápidos |
| `/eventos/` | `eventos.html` | Listado de partidos, cuotas y boleto de apuesta |
| `/cuenta/` | `cuenta.html` | Registro, login, KYC y juego responsable |

## Páginas con sesión

| Ruta | Template | Requiere login |
|------|----------|----------------|
| `/cartera/` | `cartera.html` | Sí — recarga, retiro, bono |
| `/apuestas/` | `apuestas.html` | Sí — historial y cash-out |
| `/operador/` | `operador.html` | Sí + usuario `is_staff` |

## Archivos estáticos por página

| Página | JavaScript propio |
|--------|-------------------|
| Todas | `fairbet-api.js`, `fairbet-ui.js` (vía `base.html`) |
| `/` | `fairbet-home.js` |
| `/cuenta/` | `fairbet-cuenta.js` |
| `/cartera/` | `fairbet-cartera.js` |
| `/eventos/` | `fairbet-eventos.js` |
| `/apuestas/` | `fairbet-apuestas.js` |
| `/operador/` | `fairbet-operador.js` |

## Flujo recomendado para la demo

1. **Inicio** (`/`) — contexto del proyecto.
2. **Cuenta** — registrarse y verificar KYC simulado.
3. **Cartera** — recargar soles virtuales.
4. **Eventos** — apostar simple o combinada.
5. **Apuestas** — ver boletos y probar cash-out.
6. **Operador** — dashboard staff (métricas, auditoría).

## Mobile-first

El CSS (`static/css/fairbet.css`) parte de pantallas estrechas (< 640 px)
y escala con `@media` a tablet y escritorio. Prueba siempre en DevTools móvil primero.
