# Guía 07 — Defensa oral, decoradores Django y preguntas del profesor

Documento para **estudiar** y **compartir con tu equipo**.  
Basado en lo que comentan sobre el profesor **Villegas**: pregunta **línea por línea**, nota lo que te saltas al explicar, conviene explicar por **clases y bloques**, y suele tocar **decoradores en Django**.

---

## 1. Contexto: ¿qué significa lo del chat?

| Comentario | Qué implica para ti |
|------------|---------------------|
| *“Pregunta línea por línea”* | Debes saber **qué hace cada archivo importante**, no solo “funciona en Postman”. |
| *“Te pregunta lo que nota que te saltas”* | Si solo muestras Postman y no wallet/KYC, ahí apunta. |
| *“Explica por clases y bloques”* | Orden: **modelo → servicio → vista → URL**, no leer código al azar. |
| *“Aprende decoradores en Django”* | Tema **muy probable** en la defensa. |

**No es para asustarte:** es una guía de estudio. Si lees esto y pruebas el flujo una vez, vas mucho más preparado.

---

## 2. Cómo explicar el proyecto por bloques (guion 5–8 min)

### Bloque A — Entorno (1 min)

> “Usamos Docker Compose con Django, PostgreSQL, Redis, Celery y Channels. PostgreSQL guarda datos; Redis cola y tiempo real; el avance actual es la API REST (~40 % del challenge FairBet Lab).”

Archivos: `docker-compose.yml`, `docs/GUIA_ENTORNO_Y_PROYECTO.md`

---

### Bloque B — Usuarios y KYC (1 min)

> “En `apps/users` validamos DNI de 8 dígitos y mayor de edad. El perfil tiene estados: pendiente, verificado, bloqueado, autoexcluido. Sin verificar no recarga ni apuesta.”

| Archivo | Rol |
|---------|-----|
| `validators.py` | Reglas DNI y edad |
| `models.py` | `UserProfile` |
| `views.py` | Registro, verify-kyc, /me |
| `serializers.py` | Validar JSON de entrada |

Conexión: `User` (Django) ↔ `UserProfile` (1 a 1).

---

### Bloque C — Wallet y partida doble (2 min) ⭐ suele preguntar mucho

> “No guardamos saldo en una columna. Cada movimiento crea líneas en `LedgerEntry` con DEBIT y CREDIT que suman cero. El saldo es SUM(créditos) − SUM(débitos). Usamos `Decimal`, no `float`, y `@transaction.atomic` con `select_for_update` para no gastar dos veces la misma ficha.”

| Archivo | Rol |
|---------|-----|
| `wallet/models.py` | `LedgerTransaction`, `LedgerEntry` |
| `wallet/services.py` | `recarga_simulada`, `bloquear_fondos_apuesta`, `calcular_saldo` |
| `wallet/views.py` | API balance y deposit |

---

### Bloque D — Eventos y apuestas (1 min)

> “En `apps/betting` hay eventos con mercado 1X2. Al apostar validamos cuenta, evento programado y saldo; luego bloqueamos fichas en el wallet y creamos `Bet` en estado accepted. La liquidación ganadora/perdedora es trabajo pendiente.”

| Archivo | Rol |
|---------|-----|
| `betting/models.py` | `SportEvent`, `Market`, `Bet` |
| `betting/services.py` | `colocar_apuesta_simple` |
| `betting/views.py` | Listar eventos, apostar |

---

### Bloque E — Admin y pruebas (30 s)

> “El `/admin/` es la vista del operador. Los tests en `wallet/tests` verifican partida doble e idempotencia.”

Guía admin: `06-PANEL-ADMIN-DJANGO.md`

---

## 3. Decoradores en Django — explicación fácil

### ¿Qué es un decorador?

Es una **función que envuelve otra** (o una clase) para **añadir comportamiento** sin repetir el mismo código en todos lados.

En Python se escribe con `@` encima de la función o clase:

```python
@algo
def mi_funcion():
    ...
```

Equivale a: `mi_funcion = algo(mi_funcion)`

**Frase para el profesor:**  
*“Un decorador es sintaxis para aplicar una capa extra (permisos, transacción, registro en admin) de forma declarativa.”*

---

### Decoradores que SÍ usamos en este proyecto

#### 1. `@transaction.atomic` — `wallet/services.py`, `betting/services.py`

```python
@transaction.atomic
def recarga_simulada(...):
    ...
```

| Pregunta posible | Respuesta corta |
|------------------|----------------|
| ¿Para qué sirve? | Garantiza que **todo** el movimiento de dinero en esa función sea **una sola unidad**: o se guarda todo, o no se guarda nada (rollback). |
| ¿Por qué en wallet? | Si falla la segunda línea del libro mayor, no debe quedar solo el débito sin el crédito. |
| ¿Y `select_for_update`? | Bloquea la fila del usuario en BD para que dos apuestas simultáneas no usen el mismo saldo. |

---

#### 2. `@admin.register(Modelo)` — `users/admin.py`, `wallet/admin.py`, `betting/admin.py`

```python
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    ...
```

| Pregunta posible | Respuesta corta |
|------------------|----------------|
| ¿Para qué sirve? | Le dice a Django: **muestra este modelo en el panel /admin/** con esta configuración (columnas, filtros, inlines). |
| Sin decorador | Tendrías que registrar manualmente con `admin.site.register(...)`. |

---

#### 3. `@property` — `users/models.py`, `betting/models.py`

```python
@property
def puede_apostar(self) -> bool:
    return self.status == AccountStatus.VERIFICADO
```

| Pregunta posible | Respuesta corta |
|------------------|----------------|
| ¿Para qué sirve? | Calcula un valor **como si fuera un atributo** (`profile.puede_apostar`) pero ejecutando lógica. |
| ¿Por qué no método? | Más legible y no necesitas `()`. |

---

#### 4. `@pytest.mark.django_db` y `@pytest.fixture` — `wallet/tests/test_services.py`

```python
@pytest.fixture
def usuario_verificado(db):
    ...

@pytest.mark.django_db
def test_deposito_aumenta_saldo(usuario_verificado):
    ...
```

| Pregunta posible | Respuesta corta |
|------------------|----------------|
| `@pytest.fixture` | Crea datos de prueba reutilizables (usuario verificado). |
| `@pytest.mark.django_db` | Permite que el test **use la base de datos** de Django. |

---

### Decoradores que el profesor puede nombrar aunque no los tengamos escritos con `@`

En **vistas DRF** usamos **atributos de clase**, que cumplen rol similar:

```python
class DepositView(APIView):
    permission_classes = [permissions.IsAuthenticated]
```

| Concepto | En nuestro proyecto |
|----------|---------------------|
| `permission_classes` | Solo usuarios con **Token** pueden depositar/apostar |
| `AllowAny` en registro | Cualquiera puede registrarse |

Si pregunta “¿cómo protegen el endpoint?” → **Token en header** + `IsAuthenticated`.

---

### Decoradores típicos del curso (saber definir aunque no estén en el repo aún)

| Decorador | Para qué sirve (memoria) |
|-----------|--------------------------|
| `@login_required` | Vista web: solo si inició sesión en navegador |
| `@api_view(['GET'])` | Función vista DRF con métodos HTTP permitidos |
| `@action` (ViewSet) | Ruta extra en un ViewSet |
| `@shared_task` (Celery) | Función que corre en worker en segundo plano |
| `@receiver` (signals) | Ejecutar código cuando pasa un evento del modelo |

**Frase honesta si no los usamos aún:**  
*“En el avance usamos APIView y servicios con `@transaction.atomic`; Celery tasks las agregaremos para liquidación programada.”*

---

## 4. Preguntas probables del profesor (con respuesta sugerida)

### Sobre el negocio

| Pregunta | Respuesta sugerida |
|----------|-------------------|
| ¿Por qué moneda virtual? | Es educativo; cumple Ley 31557 como referencia sin ser casa de apuestas real. |
| ¿Dónde está el footer legal? | `templates/base.html` y mensaje en respuesta de apuesta. |
| ¿Cómo validan mayor de edad? | `fecha_nacimiento` en registro + `es_mayor_de_edad()` en `validators.py`. |
| ¿Qué es KYC simulado? | Estados en `UserProfile`; verify-kyc o admin cambia a `verificado`. |

### Sobre dinero y wallet ⭐

| Pregunta | Respuesta sugerida |
|----------|-------------------|
| ¿Dónde guardan el saldo? | **En ningún lado fijo**; se calcula del ledger. |
| ¿Qué es partida doble? | Mínimo débito + crédito mismo monto; suma global cero por transacción. |
| ¿Por qué no `float`? | Errores de redondeo; usamos `Decimal(18,4)`. |
| ¿Qué pasa si dos apuestas al mismo tiempo? | `transaction.atomic` + `select_for_update` en el usuario. |
| ¿Qué es idempotency_key? | Reintentar la misma petición no duplica recarga/apuesta. |

### Sobre Docker / stack

| Pregunta | Respuesta sugerida |
|----------|-------------------|
| ¿Para qué PostgreSQL? | Datos persistentes y transacciones serias. |
| ¿Para qué Redis? | Cola Celery y (futuro) Channels tiempo real. |
| ¿Por qué Docker? | Mismo entorno en todo el equipo y en la máquina del profesor. |

### Sobre código línea por línea

| Pregunta | Respuesta sugerida |
|----------|-------------------|
| Explique `recarga_simulada` | Valida perfil → bloquea usuario → crea transacción → 2 `LedgerEntry` CREDIT wallet / DEBIT casa. |
| Explique `colocar_apuesta_simple` | Valida reglas → crea `Bet` → llama wallet para bloquear → si falla wallet, borra bet. |
| ¿Qué hace `serializers.py`? | Valida entrada JSON antes de tocar modelos. |
| ¿Qué hace `manage.py`? | Puerta de comandos: migrate, runserver, seed_demo, test. |

### Sobre lo que aún NO está hecho (honestidad = puntos)

| Pregunta | Respuesta sugerida |
|----------|-------------------|
| ¿Liquidan apuestas ganadas? | Aún no; Bet queda en `accepted`; siguiente sprint. |
| ¿Cuotas en vivo? | Channels configurado; falta WebSocket y lógica in-play. |
| ¿Auditoría hash? | App `audit` preparada; pendiente Nivel 3. |
| ¿80 % cobertura? | Tests básicos wallet; falta ampliar betting y Hypothesis. |

### Trampa: “¿Ustedes escribieron todo esto?”

Respuesta recomendada (si usaron IA como apoyo):

> “El entorno y la estructura las armamos con ayuda de IA documentada en `anti-ai-disclosure.md`, pero podemos explicar wallet, KYC y el flujo en vivo; los tests y Postman los ejecutamos nosotros.”

---

## 5. Qué NO te conviene saltarte en la explicación

Si solo muestras Postman, el profesor puede preguntar:

1. **`wallet/services.py`** — partida doble  
2. **`users/validators.py`** — DNI y edad  
3. **`betting/services.py`** — validaciones antes de apostar  
4. Por qué **`@transaction.atomic`**  
5. Diferencia **Token** vs **admin login**  

Ten abiertos esos 4 archivos durante la defensa.

---

## 6. Cómo compartir todo el trabajo con tus compañeros

### Opción A — Carpeta comprimida (rápido, sin Git)

1. Cierra Docker o deja corriendo (no importa para copiar código).  
2. Copia la carpeta `TALLER_LENGUAJE` **excepto** cosas pesadas:
   - No envíes: carpetas `__pycache__`, `.pytest_cache`, volúmenes Docker internos.  
3. Clic derecho → **Comprimir en ZIP**.  
4. Sube a **Drive / OneDrive / WhatsApp (si pesa poco)** y pasa el enlace.

**Incluye siempre:**
- Todo el código fuente  
- `docs/` (guías)  
- `.env.example` (plantilla)  
- **No incluyas** tu `.env` con claves si las cambiaron (cada uno copia `.env.example` → `.env`)

**Mensaje para el grupo:**

> “Descarguen el ZIP, instalen Docker Desktop, copien `.env.example` a `.env`, y ejecuten `docker compose up -d --build`. Guía: `docs/guias/04-COMO-PROBAR-EL-AVANCE.md`.”

---

### Opción B — Git / GitHub (recomendado para el curso)

El enunciado pide **repositorio Git** con commits y Conventional Commits.

**Pasos para quien tiene el proyecto (tú):**

```powershell
cd C:\Users\JORDAN\Documents\TALLER_LENGUAJE
git init
git add .
git commit -m "feat: avance 40% FairBet Lab con API y guías"
```

Crear repo en GitHub (vacío) → copiar URL →:

```powershell
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```

**Invitar compañeros:** en GitHub → **Settings → Collaborators** → agregar usuarios.

**Compañeros clonan:**

```powershell
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
copy .env.example .env
docker compose up -d --build
```

Ventajas: historial, commits por persona, cumple entregable del challenge.

---

### Opción C — Misma red / USB

- Pendrive con el ZIP del proyecto.  
- Carpeta compartida en red local del laboratorio.

---

## 7. Qué debe tener cada compañero instalado

| Software | Obligatorio |
|----------|-------------|
| Docker Desktop | Sí |
| VS Code | Recomendado |
| Postman | Recomendado para probar API |
| Git | Si usan Opción B |

**No necesitan** instalar Python ni PostgreSQL en Windows si usan solo Docker.

---

## 8. División sugerida del trabajo (para el equipo)

| Persona / rol | Puede encargarse de |
|---------------|---------------------|
| A | Explicar wallet + decorador `@transaction.atomic` |
| B | Explicar users/KYC + DNI |
| C | Explicar betting + demo Postman |
| D | Docker + admin + documentación ADR |

Todos deben poder ejecutar: `docker compose up`, registro, KYC, deposit, apuesta.

---

## 9. Checklist antes de presentar con Villegas

- [ ] Sé explicar **3 decoradores** del proyecto: `@transaction.atomic`, `@admin.register`, `@property`  
- [ ] Sé dibujar flujo: registro → KYC → recarga → apuesta → ledger  
- [ ] Abrí `wallet/services.py` y expliqué sin leerlo palabra por palabra memorizada  
- [ ] Sé qué está **hecho** y qué **falta** (sin mentir)  
- [ ] Compañeros tienen el repo/ZIP y pueden levantar Docker  
- [ ] Leí `06-PANEL-ADMIN-DJANGO.md` y esta guía  

---

## 10. Índice de guías del equipo

| Archivo | Tema |
|---------|------|
| `00-INDICE.md` | Índice |
| `01-PASO-USUARIOS-KYC.md` | Usuarios |
| `02-PASO-WALLET.md` | Wallet |
| `03-PASO-EVENTOS-APUESTAS.md` | Apuestas |
| `04-COMO-PROBAR-EL-AVANCE.md` | Postman |
| `05-QUE-FALTA-PARA-TERMINAR.md` | Roadmap |
| `06-PANEL-ADMIN-DJANGO.md` | Admin |
| **`07-DEFENSA-ORAL-Y-PREGUNTAS-PROFESOR.md`** | **Esta guía** |

---

**Fin.** Comparte este archivo con tu equipo junto al ZIP o el enlace de GitHub.
