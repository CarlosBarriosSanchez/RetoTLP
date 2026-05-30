# ADR-002 — Autenticación por Token

**Estado:** Aceptado  
**Fecha:** 2026-05-29

## Contexto

La interfaz web consume la API REST desde JavaScript (`fetch`).
Necesitamos identificar al usuario sin complicar el frontend.

## Decisión

Usar **TokenAuthentication** de DRF (cabecera `Authorization: Token …`).

El token se guarda en `localStorage` del navegador tras registro o login.

No usamos `SessionAuthentication` en la API porque exige CSRF en peticiones
POST y bloqueaba flujos si el usuario había visitado `/admin/` antes.

## Motivos

- Simple de implementar para un equipo junior.
- Funciona igual desde cualquier página HTML del proyecto.
- El token persiste al recargar la página (mejor UX en demo).

## Consecuencias

- Positivo: el cliente API (`fairbet-api.js`) es pequeño y legible.
- Positivo: cada integrante prueba endpoints con curl o Postman fácilmente.
- Negativo: `localStorage` no es ideal para producción real (XSS).
- Nota: esto es un **simulador educativo**, no una app bancaria.

## Alternativa descartada

Sesión con cookies + CSRF: más segura en producción, pero añade fricción
en un frontend multipágina sin framework unificado.
