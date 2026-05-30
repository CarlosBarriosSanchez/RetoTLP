# Guía del entorno FairBet Lab  
## Para estudiar y explicárselo a tu profesor (palabras sencillas)

**Autor del entorno:** configuración inicial del proyecto  
**Fecha:** mayo 2026  
**Proyecto:** Challenge FairBet Lab — simulador educativo de apuestas con moneda virtual  

---

## 1. ¿Qué es este proyecto en una frase?

Es una **aplicación web de práctica** donde los usuarios apuestan **fichas virtuales** (como monedas de un juego, **sin dinero real**) en partidos deportivos. El curso lo usa para enseñar cómo construir un sistema **serio**: que no pierda fichas por errores, que respete límites de juego responsable y que deje **rastro de todo** lo que pasa, como pediría una regulación (Ley 31557 en Perú), pero **sin ser una casa de apuestas real**.

---

## 2. ¿Qué hicimos en el entorno (sin programar el reto completo)?

Montamos la **“cocina”** del proyecto: los programas y servicios que necesitas para desarrollar y entregar el challenge. **Todavía no está hecha** la lógica del wallet, las apuestas, el KYC, etc.; eso lo irán implementando ustedes en las carpetas `apps/`.

| Lo que creamos | ¿Para qué sirve? |
|----------------|------------------|
| **Docker Compose** | Levanta todos los servicios con un solo comando |
| **Django 5** | Framework web y API (backend) |
| **PostgreSQL** | Base de datos donde se guardan usuarios, apuestas, movimientos |
| **Redis** | Cola rápida para tareas y para tiempo real |
| **Celery + Celery Beat** | Trabajos en segundo plano y programados |
| **Daphne + Channels** | Conexiones en tiempo real (cuotas en vivo) |
| **Carpetas `apps/`** | Donde irá cada parte del negocio |
| **`.env`** | Contraseñas y configuración (no se sube a Git) |
| **Esta guía** | Para que entiendas y expliques cada pieza |

---

## 3. ¿Qué es Docker y por qué lo pide el curso?

**Docker** empaqueta una aplicación con todo lo que necesita (Python, librerías, configuración) en **contenedores**: cajas aisladas que corren igual en tu laptop, en la de un compañero y en el servidor del profesor.

**¿Por qué lo necesitamos aquí?**

1. El reto pide **varios programas a la vez** (base de datos, Redis, Django, Celery…). Instalarlos a mano en Windows suele dar errores.
2. Con `docker compose up` todos arrancan **conectados entre sí**.
3. El profesor puede reproducir tu entorno leyendo tu `docker-compose.yml`.

**Frase para el profesor:**  
*“Usamos Docker para que el stack obligatorio del enunciado (Django, PostgreSQL, Redis, Celery, Channels) sea reproducible y no dependa de instalaciones manuales en cada máquina.”*

---

## 4. Cada servicio del `docker-compose.yml` explicado

### 4.1 `db` (PostgreSQL)

- **Qué es:** la base de datos relacional.
- **Qué guardará:** usuarios, apuestas, movimientos del wallet, auditoría, etc.
- **Puerto 5432:** para conectarte con herramientas como DBeaver (opcional).
- **Volumen `postgres_data`:** los datos **no se borran** al apagar el contenedor (solo si haces `docker compose down -v`).

**Para el profesor:** *“PostgreSQL es el almacén persistente; el enunciado lo exige explícitamente.”*

---

### 4.2 `redis`

- **Qué es:** base de datos en memoria, muy rápida.
- **Para qué la usamos aquí (3 cosas):**
  1. **Cola de Celery:** mensajes del tipo “liquida esta apuesta”, “envía alerta”.
  2. **Resultados de tareas** de Celery.
  3. **Channel layers** de Django Channels: repartir mensajes de WebSockets entre procesos.

**Para el profesor:** *“Redis no reemplaza a PostgreSQL; complementa para velocidad y para tiempo real.”*

---

### 4.3 `web` (Django)

- **Qué es:** el servidor principal de la API y del panel admin.
- **Puerto 8000:** http://localhost:8000
- **Comando al iniciar:** ejecuta migraciones y `runserver`.
- **Carpeta montada `/app`:** el código de tu PC se ve dentro del contenedor; si editas en VS Code, Django recarga.

**Endpoint de prueba:** `GET /api/health/` → responde que el entorno está vivo.

**Para el profesor:** *“Es el núcleo HTTP del sistema; DRF y las apps de negocio vivirán aquí.”*

---

### 4.4 `celery` (worker)

- **Qué es:** proceso que **ejecuta tareas pesadas o lentas** sin bloquear al usuario.
- **Ejemplos futuros en FairBet:** liquidar muchas apuestas al finalizar un partido, generar reporte CSV, revisar reglas anti-fraude.

**Para el profesor:** *“Separamos lo síncrono (respuesta HTTP rápida) de lo asíncrono (trabajo en cola vía Redis).”*

---

### 4.5 `celery-beat`

- **Qué es:** el **reloj** que programa tareas periódicas.
- **Ejemplo futuro:** cada minuto revisar eventos que pasaron a `en_vivo`.

**Para el profesor:** *“Celery Beat + django-celery-beat permite persistir horarios en la base de datos.”*

---

### 4.6 `channels` (Daphne)

- **Qué es:** servidor **ASGI** para HTTP + **WebSockets**.
- **Puerto 8001:** tiempo real separado del 8000 (organización clara; en producción se puede unificar detrás de un proxy).
- **Para qué en el reto:** actualizar **cuotas en vivo** cuando el partido está `en_vivo` (Nivel 2 del enunciado).

**Para el profesor:** *“Django Channels sobre Daphne cumple el requisito de odds en tiempo real del challenge.”*

---

## 5. Estructura de carpetas del código

```
TALLER_LENGUAJE/
├── config/                 → Configuración global (settings, urls, celery, asgi)
├── apps/
│   ├── users/              → Registro, edad, DNI, estados KYC, autoexclusión
│   ├── wallet/             → Partida doble, fichas, recargas/retiros simulados
│   ├── betting/            → Eventos, mercados 1X2, apuestas, liquidación
│   └── audit/              → Cadena de hashes inmutable (nivel 3)
├── templates/base.html     → Footer legal obligatorio del enunciado
├── docs/                   → Esta guía, ADRs, bocetos, lecciones (por crear)
├── docker-compose.yml      → Define todos los servicios
├── Dockerfile              → Imagen Python con dependencias
├── requirements.txt        → Librerías Python del stack obligatorio
├── manage.py               → Comandos Django (migrate, test, etc.)
├── index.html              → Enunciado del challenge (referencia)
└── .env                    → Variables secretas (NO subir a Git)
```

**Importante:** las apps tienen archivos `models.py` con comentarios **TODO**; la lógica del reto **aún no está implementada**. El entorno solo deja listo **dónde** va cada cosa.

---

## 6. Archivos clave y por qué existen

### `requirements.txt`

Lista las librerías que exige el enunciado:

| Librería | Uso |
|----------|-----|
| Django + DRF | Web y API REST |
| psycopg2 | Conectar Django con PostgreSQL |
| redis, celery | Colas y tareas |
| channels, daphne, channels-redis | Tiempo real |
| hypothesis, pytest | Pruebas e invariantes financieras |
| python-decouple | Leer variables del `.env` |

---

### `config/settings.py`

Decisiones ya tomadas para alinearse al enunciado:

- **`DECIMAL_MAX_DIGITS = 18`** y **`DECIMAL_PLACES = 4`**: preparado para dinero sin `float`.
- **`DATABASES` → PostgreSQL**: no SQLite en producción del reto.
- **`CHANNEL_LAYERS` → Redis**: WebSockets escalables.
- **`CELERY_*`**: broker y resultados en Redis.
- **`LANGUAGE_CODE = es-pe`**, **`TIME_ZONE = America/Lima`**: contexto local.

**Para el profesor:** *“La configuración refleja restricciones del PDF: Decimal, Postgres, Redis, Channels desde el día uno.”*

---

### `.env` y `.env.example`

- **`.env`:** valores reales en tu máquina (contraseña de BD, `SECRET_KEY`). Está en `.gitignore`.
- **`.env.example`:** plantilla para que otro integrante copie y cree su `.env`.

**Para el profesor:** *“Separamos configuración del código; buena práctica de seguridad.”*

---

### `templates/base.html`

Incluye el texto obligatorio del footer:

> *Plataforma educativa con moneda virtual. No constituye una casa de apuestas.*

**Para el profesor:** *“Cumplimos la restricción explícita de mostrar el disclaimer en las pantallas.”*

---

## 7. Cómo encaja esto con lo que pide el enunciado (`index.html`)

| Requisito del PDF | ¿Dónde lo preparamos? |
|-------------------|------------------------|
| Django 5 + DRF | `web`, `config/`, `requirements.txt` |
| PostgreSQL | servicio `db` |
| Redis | servicio `redis` |
| Celery | servicios `celery`, `celery-beat` |
| Django Channels | servicio `channels`, `config/asgi.py` |
| Decimal, no float | `settings.py` + implementación futura en `wallet` |
| Apps wallet y betting | carpetas `apps/wallet`, `apps/betting` |
| Cobertura 80 %, Hypothesis | `pytest.ini`, dependencias en `requirements.txt` |
| docker-compose en entrega | `docker-compose.yml` |
| Footer legal | `templates/base.html` |
| ADRs, bocetos, anti-ai | carpetas `docs/` (ustedes las completan) |

Lo que **falta por programar** (y es la mayor parte de la nota): KYC, `LedgerEntry`, apuestas, juego responsable, auditoría, tests, etc.

---

## 8. Cómo arrancar el entorno (paso a paso)

### Requisitos previos

1. **Docker Desktop** abierto y en estado *Running*.
2. **VS Code** (opcional pero recomendado).

### Nombre en Docker Desktop

Por defecto Docker usa el **nombre de la carpeta** (`TALLER_LENGUAJE` → `taller_lenguaje`).  
En este proyecto definimos en `docker-compose.yml`:

```yaml
name: simulador-apuestas-deportivas
```

Así en Docker Desktop verás **simulador-apuestas-deportivas** (sin espacios: Docker no permite espacios en el nombre del proyecto).

### Comandos

```powershell
cd C:\Users\JORDAN\Documents\TALLER_LENGUAJE
docker compose up -d --build
```

Espera unos minutos la primera vez (descarga imágenes y construye).

### Comprobar que funciona

1. Navegador: http://localhost:8000/api/health/  
   Debe verse JSON con `"status": "ok"`.
2. Terminal:

```powershell
docker compose ps
```

Todos los servicios deben estar `running` o `healthy`.

### Crear usuario administrador (cuando quieras entrar al admin)

```powershell
docker compose exec web python manage.py createsuperuser
```

Luego: http://localhost:8000/admin/

### Detener todo

```powershell
docker compose down
```

---

## 9. Guion sugerido para explicar al profesor (3–5 minutos)

Puedes leer esto casi tal cual:

> **Profesor,** estamos desarrollando **FairBet Lab**, un simulador educativo de apuestas con fichas virtuales, sin dinero real, según el challenge del curso y la Ley 31557 como referencia de cumplimiento.
>
> **Primero**, montamos el entorno con **Docker Compose** porque el enunciato exige **Django, PostgreSQL, Redis, Celery y Channels** trabajando juntos. Docker nos permite levantar los seis servicios con un solo comando y que todo el equipo tenga la misma configuración.
>
> **PostgreSQL** guarda los datos importantes de forma permanente: usuarios, apuestas y movimientos contables.
>
> **Redis** no guarda el negocio principal; lo usamos como cola rápida para **Celery** (tareas en segundo plano) y para **Channels** (actualizar cuotas en tiempo real por WebSocket).
>
> El contenedor **web** corre **Django y Django REST Framework** en el puerto 8000; ahí irá la API y el admin.
>
> **Celery** procesará trabajos que no deben bloquear al usuario, por ejemplo liquidar apuestas cuando termina un partido.
>
> **Daphne con Channels** en el puerto 8001 prepara las **cuotas en vivo**, que es parte del nivel avanzado del reto.
>
> Organizamos el código en apps: **users** (KYC y autoexclusión), **wallet** (partida doble, sin guardar saldo fijo sino calcularlo), **betting** (eventos y apuestas) y **audit** (registro inmutable con hashes).
>
> En configuración ya dejamos **Decimal con 4 decimales** porque el enunciato prohíbe `float` para dinero.
>
> **Lo que sigue** es implementar la lógica del PDF: partida doble, máquina de estados de la apuesta, límites de juego responsable y pruebas con cobertura del 80 %. El entorno es la base; el negocio lo estamos construyendo encima con TDD y ADRs en la carpeta `docs/`, como pide la política de autoría del challenge.

---

## 10. Preguntas que el profesor podría hacer (y respuestas simples)

**¿Por qué no usan SQLite?**  
Porque el reto exige PostgreSQL y porque con dinero simulado y muchas apuestas concurrentes necesitamos transacciones serias (`select_for_update`).

**¿Qué pasa si dos usuarios apuestan al mismo tiempo con la última ficha?**  
Eso se resolverá en `wallet` con transacciones atómicas y bloqueo en base de datos; el entorno ya usa Postgres para permitirlo.

**¿Docker es obligatorio o solo comodidad?**  
El entregable pide `docker-compose` en el repositorio; es parte de la evaluación y de la reproducibilidad.

**¿Ya está terminado el challenge?**  
No. Solo está el **esqueleto** y los servicios corriendo. Falta implementar reglas de negocio, tests, ADRs, diagramas y demo.

**¿Dónde está la partida doble?**  
Pendiente en `apps/wallet/models.py`. La idea: cada movimiento genera al menos un débito y un crédito que suman cero.

**¿Por qué hay dos puertos 8000 y 8001?**  
8000 = HTTP normal (API). 8001 = servidor con WebSockets (tiempo real). Se puede unificar más adelante; así es más fácil de depurar al inicio.

---

## 11. Próximos pasos de implementación (orden recomendado)

1. **users:** registro, validar DNI peruano, mayor de 18, estados de cuenta.  
2. **wallet:** modelo `LedgerEntry`, recarga simulada, calcular saldo.  
3. **betting:** eventos, mercado 1X2, apuesta simple, liquidación.  
4. **Juego responsable:** límites y autoexclusión bloqueantes.  
5. **Tests** con pytest + hypothesis en wallet y betting.  
6. **Nivel 2:** combinadas, in-play, cash-out, Channels.  
7. **Nivel 3:** auditoría con hash, dashboard, anti-fraude.  
8. **Documentación:** ADRs, ER, máquina de estados, video demo.

---

## 12. Registro de lo que hizo la IA en este entorno (para tu `anti-ai-disclosure.md`)

Puedes copiar y adaptar:

```markdown
## Asistencia IA — configuración inicial del entorno

- **Qué se pidió:** crear docker-compose, proyecto Django vacío, guía explicativa.
- **Qué generó la IA:** estructura de carpetas, settings base, Dockerfile, esta guía.
- **Qué NO generó la IA:** lógica de wallet, apuestas, KYC, tests de negocio, ADRs de decisiones propias.
- **Compromiso:** implementar y defender en walkthrough el código de negocio escrito por el equipo.
```

---

## 13. Solución de problemas frecuentes

| Problema | Causa probable | Qué hacer |
|----------|----------------|-----------|
| `cannot find pipe dockerDesktopLinuxEngine` | Docker Desktop apagado | Abrir Docker Desktop y esperar |
| Puerto 8000 ocupado | Otra app usando 8000 | Cambiar puerto en `docker-compose.yml` o cerrar la otra app |
| `web` reinicia en bucle | Error en migrate o settings | `docker compose logs web` |
| `Conflict. container name ... already in use` | Cambiaste el nombre del proyecto pero quedaron contenedores viejos | `docker compose -p taller_lenguaje down` y `docker compose up -d --build` |
| Cambios en código no se ven | Caché o no guardaste | Guardar archivo; Django recarga solo en modo dev |

---

**Fin de la guía.**  
Cuando implementes cada parte, añade al final de este documento una sección “Bitácora” con fecha y qué aprendiste, como pide el enunciado en `docs/lecciones.md`.
