# Guía 01 — Usuarios y KYC (Conoce tu cliente)

## ¿Qué problema resuelve?

Antes de apostar, el sistema debe saber **quién eres** y si **cumples requisitos legales simulados**:

- Mayor de 18 años  
- DNI peruano válido  
- Cuenta en un estado permitido (verificada, no bloqueada, no autoexcluida)

En el enunciado esto se llama **KYC simulado** (no es un banco real, pero imita el flujo).

---

## Archivos de esta parte y para qué sirven

| Archivo | Sirve para |
|---------|------------|
| `apps/users/models.py` | Guarda `UserProfile`: DNI, fecha nacimiento, `status` |
| `apps/users/validators.py` | Valida DNI (dígito verificador) y edad ≥ 18 |
| `apps/users/serializers.py` | Convierte datos JSON ↔ Python en el registro |
| `apps/users/views.py` | Endpoints: registrar, ver perfil, verificar KYC |
| `apps/users/urls.py` | Rutas `/api/users/...` |
| `apps/users/admin.py` | Ver perfiles en el panel `/admin/` |

---

## ¿Con qué se conecta?

```
auth.User (Django, tabla de login)
      │
      │ OneToOne
      ▼
UserProfile (nuestra app users)
      │
      ├── wallet usa profile.status para permitir recarga
      └── betting usa profile.puede_apostar
```

**PostgreSQL** guarda todo en tablas `auth_user` y `users_userprofile`.

---

## Estados de cuenta (`status`)

| Valor | Significado | ¿Puede apostar? |
|-------|-------------|-----------------|
| `pendiente_verificacion` | Recién registrado | No |
| `verificado` | KYC simulado OK | Sí |
| `bloqueado` | Admin bloqueó | No |
| `autoexcluido` | Juego responsable | No |

---

## Flujo que debes poder explicar

1. Usuario hace `POST /api/users/register/` con username, password, DNI, fecha nacimiento.  
2. El sistema valida **formato DNI (8 dígitos)** y edad en `validators.py`.  
   - Tu DNI real `77814916` es válido.  
   - El dígito verificador de la **tarjeta física** (módulo 11) es otro cálculo y no se confunde con el 8.º dígito del número.  
3. Se crea `User` + `UserProfile` en estado **pendiente_verificacion**.  
4. Se devuelve un **token** para las siguientes peticiones.  
5. Para la demo: `POST /api/users/verify-kyc/` pasa a **verificado** (en producción lo haría un admin).

---

## Frase para el profesor

> *"Separamos el login de Django (`User`) del perfil regulatorio (`UserProfile`). El KYC no es un PDF real: validamos reglas (edad, DNI) y un estado que bloquea apuestas hasta verificar."*

---

## Qué falta en esta parte (para el 100 %)

- Autoexclusión temporal 7/30/90 días con cron  
- Panel admin real de revisión KYC (no botón automático del usuario)  
- Bloqueo por intentos fallidos  
