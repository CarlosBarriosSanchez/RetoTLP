# Guía de instalación

Pasos para levantar **FairBet Lab** en tu máquina con Docker.

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y en ejecución.
- Git (para clonar el repositorio).

## 1. Clonar y configurar entorno

```bash
git clone <url-del-repo>
cd RetoTLP-2
cp .env.example .env
```

El archivo `.env` ya trae valores por defecto válidos para desarrollo local.
Cambia `SECRET_KEY` si vas a desplegar fuera de tu PC.

## 2. Levantar servicios

```bash
docker compose up -d --build
```

Esto inicia:

| Servicio | Puerto | Función |
|----------|--------|---------|
| `web` | 8000 | Django (páginas + API REST) |
| `channels` | 8001 | WebSockets (cuotas en vivo) |
| `db` | 5432 | PostgreSQL |
| `redis` | 6379 | Celery + Channels |
| `celery` | — | Worker de tareas |
| `celery-beat` | — | Tareas programadas |

## 3. Datos de demo (opcional)

```bash
docker compose exec web python manage.py seed_demo
```

Crea partidos de ejemplo con mercados 1X2, over/under, BTTS y hándicap.

## 4. Comprobar que funciona

- Página de inicio: http://localhost:8000/
- Health check API: http://localhost:8000/api/health/
- Admin Django: http://localhost:8000/admin/ (crea superusuario antes)

```bash
docker compose exec web python manage.py createsuperuser
```

## 5. Detener el entorno

```bash
docker compose down
```

Para borrar también la base de datos: `docker compose down -v`

## Desarrollo sin Docker (avanzado)

1. Python 3.12, PostgreSQL y Redis instalados localmente.
2. `pip install -r requirements.txt`
3. Ajusta `POSTGRES_HOST=localhost` y `REDIS_URL` en `.env`.
4. `python manage.py migrate && python manage.py runserver`

## Problemas frecuentes

| Síntoma | Solución |
|---------|----------|
| Puerto 8000 ocupado | Cambia el mapeo en `docker-compose.yml` |
| `db` no arranca | Espera el healthcheck o reinicia compose |
| Sin eventos en la web | Ejecuta `seed_demo` |
