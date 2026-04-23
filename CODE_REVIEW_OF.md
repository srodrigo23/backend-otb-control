# Code Review — OTB Web App Backend

**Revisor:** Staff/Senior Software Engineer  
**Fecha:** 2026-04-18  
**Branch:** `code-review`  
**Stack:** Python 3.11+ · FastAPI 0.116 · SQLAlchemy 2.0 · PostgreSQL (Supabase) / SQLite · python-jose · bcrypt  
**Dominio:** Sistema de gestión comunitaria (vecinos, medidores de agua, deudas, pagos, reuniones)

---

## Resumen Ejecutivo

El proyecto implementa una API REST funcional con un modelo de dominio razonablemente bien estructurado. Sin embargo, presenta **vulnerabilidades de seguridad críticas que lo hacen inapto para producción en su estado actual**: autenticación completamente rota, todos los endpoints expuestos sin protección, y credenciales de producción hardcodeadas en el repositorio. A nivel arquitectónico hay deuda técnica significativa (duplicación masiva, acoplamiento fuerte en rutas, violaciones SOLID) pero es recuperable. El problema más urgente no es refactoring — es que la API es hoy mismo un vector de ataque abierto.

---

## Tabla de Hallazgos

| # | Severidad | Área | Hallazgo |
|---|-----------|------|----------|
| C-01 | **CRÍTICO** | Seguridad | JWT firmado con el nombre del algoritmo, no con la clave secreta |
| C-02 | **CRÍTICO** | Seguridad | `verify_password()` roto — autenticación no funciona |
| C-03 | **CRÍTICO** | Seguridad | Cero endpoints protegidos por autenticación |
| C-04 | **CRÍTICO** | Seguridad | Endpoint destructivo de migración financiera completamente abierto |
| C-05 | **CRÍTICO** | Seguridad | Credenciales de producción en `.env` comprometidas en el repo |
| A-01 | **Alto** | Bug / Datos | Operación de pago sin transacción atómica — estado financiero inconsistente |
| A-02 | **Alto** | Bug | Balance negativo en pagos no validado |
| A-03 | **Alto** | Bug | Consumo de agua calculado por `id`, no por fecha — lecturas fuera de orden producen consumos incorrectos |
| A-04 | **Alto** | Código Muerto | Referencias a `models.Item` y `models.User` (vía CRUD) que no existen → crash en runtime |
| A-05 | **Alto** | Arquitectura | Endpoint `POST /{collect_debt_id}/payments` usa query params para cuerpo complejo — `list[dict]` es inviable como query param en FastAPI |
| M-01 | **Medio** | Performance | `get_neighbors()` ignora `skip`/`limit` — carga toda la tabla sin paginación |
| M-02 | **Medio** | Calidad | Duplicación masiva de serialización manual de respuestas (viola DRY/SRP) |
| M-03 | **Medio** | Calidad | Conversión de fechas como strings en lugar de usar tipos nativos Pydantic |
| M-04 | **Medio** | Arquitectura | Lógica de negocio en routers (violación SRP / Arquitectura por capas) |
| M-05 | **Medio** | Bug | `read_neighbors` retorna `{'success': 'True'}` cuando no hay vecinos — rompe contratos de API |
| M-06 | **Medio** | Arquitectura | Route conflict en `/meets/` — trailing slash inconsistente |
| M-07 | **Medio** | Seguridad | `SECRET_KEY = "supersecretkey"` — clave JWT predecible |
| B-01 | **Bajo** | Testing | Sin suite de tests — solo scripts utilitarios ad-hoc |
| B-02 | **Bajo** | Calidad | `from datetime import datetime` dentro de funciones (import en scope de función) |
| B-03 | **Bajo** | Calidad | Comentario `# Monto total en centavos` desactualizado en schema |
| B-04 | **Bajo** | DevOps | Sin gestión de migraciones (Alembic ausente) — `create_all()` en startup |
| B-05 | **Bajo** | Calidad | Typo en tag del router: `tags=['Dets']` en `debts.py` |

---

## Hallazgos Detallados

---

### C-01 — CRÍTICO · Seguridad: JWT firmado con el nombre del algoritmo en lugar de la clave secreta

**Archivo:** `app/main.py:49`

```python
# BUGGY — tal como está en producción
return jwt.encode(to_encode, settings.ALGORITHM, algorithm=settings.ALGORITHM)
#                              ^^^^^^^^^^^^^^^^
#                              Esto es "HS256", no la clave secreta
```

**Debería ser:**
```python
return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

**Impacto:** El JWT se firma usando la cadena `"HS256"` como clave HMAC. Esta clave es completamente pública y predecible — cualquier persona que sepa que la API usa HS256 (estándar de la industria, deducible en segundos) puede forjar tokens válidos para cualquier usuario, incluido un administrador. Esto invalida completamente el mecanismo de autenticación.

**Explotación:**
```python
import jwt
# Forjar token de admin con clave conocida "HS256"
token = jwt.encode({"sub": "admin", "exp": 9999999999}, "HS256", algorithm="HS256")
# Este token pasa la verificación en /me
```

**Fix:** Corregir la llamada a `jwt.encode`. Rotar `SECRET_KEY` inmediatamente ya que todos los tokens emitidos hasta ahora son comprometidos.

---

### C-02 — CRÍTICO · Seguridad: `verify_password()` está roto

**Archivo:** `app/models/user.py:16-18`

```python
def verify_password(self, password):
    pwhash = bcrypt.hashpw(password.encode('utf-8'), self.password_hash)
    return pwhash == self.password_hash
```

**Problemas:**

1. `bcrypt.hashpw` espera `bytes` como salt. `self.password_hash` es un `String` SQLAlchemy — si viene de PostgreSQL es `str`, lo que causa `TypeError` en runtime.
2. Incluso si se corrigiera el tipo, la API correcta de bcrypt es `bcrypt.checkpw()`, no `bcrypt.hashpw()` con comparación manual.
3. La comparación `pwhash == self.password_hash` es una comparación de `bytes` contra `str` — siempre `False`.

**Consecuencia probable:** El endpoint `/login` retorna 500 (TypeError) o `{'success': 'False'}` para cualquier credencial. La autenticación está efectivamente deshabilitada pero silenciosamente, dando una falsa sensación de seguridad.

**Fix:**
```python
def verify_password(self, password: str) -> bool:
    return bcrypt.checkpw(
        password.encode('utf-8'),
        self.password_hash.encode('utf-8')
    )
```

También verificar que al crear usuarios se use `bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()` para almacenar como string.

---

### C-03 — CRÍTICO · Seguridad: Cero endpoints protegidos por autenticación

**Archivos:** Todos los routers (`neighbors.py`, `meets.py`, `measures.py`, `collect_debts.py`, `debts.py`)

Existe infraestructura de JWT (`/login`, `/me`), pero **ningún endpoint de negocio verifica el token**. Cualquier persona con acceso a la URL puede:

- Leer todos los vecinos, deudas y datos financieros: `GET /neighbors`, `GET /neighbors/{id}/debts/all`
- Crear, modificar y eliminar vecinos, reuniones, mediciones
- Registrar pagos arbitrarios: `POST /collect-debts/{id}/payments`
- Ver datos personales (CI, teléfono, email de vecinos): sin restricción alguna

**Fix — Dependency de autenticación reutilizable:**
```python
# app/dependencies.py
from fastapi import Cookie, HTTPException, status
from jose import jwt, JWTError
from .settings import settings

def get_current_user(access_token: str = Cookie(None)) -> str:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

```python
# En cada router que requiera autenticación:
@router.get("")
def read_neighbors(
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user)  # protege el endpoint
):
    ...
```

---

### C-04 — CRÍTICO · Seguridad / Datos: Endpoint de migración financiera completamente abierto

**Archivo:** `app/routers/debts.py:14-68`

```python
@router.post("/migrate-to-bolivianos")
def migrate_debtsto_bolivianos(db: Session = Depends(get_db)):
    # Sin autenticación. Divide TODOS los montos por 100.
    debts = db.query(models.DebtItem).all()
    for debt in debts:
        debt.amount = debt.amount / 100  # Operación destructiva e irreversible
```

**Problemas:**
1. Sin autenticación — cualquier persona puede ejecutarlo.
2. Sin idempotencia — ejecutarlo dos veces divide por 10.000, destruyendo todos los registros financieros.
3. Sin confirmación ni parámetro de "dry run".
4. El endpoint lleva el prefijo `/debts` que es un path de negocio normal — fácil de descubrir.

**Fix inmediato:** Remover este endpoint. La migración ya ocurrió (es una operación de un uso). Si se necesita mantener, moverlo detrás de autenticación de ADMIN, agregar flag de idempotencia (e.g., verificar si ya fue ejecutado), y considerarlo como script de migración fuera de la API.

---

### C-05 — CRÍTICO · Seguridad: Credenciales de producción en el repositorio

**Archivo:** `.env` (línea 1)

```
db_url_supabase="postgresql://postgres.vnuioejzhnwuokpzwnqn:otbcentralizadoqwerty@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
SECRET_KEY = "supersecretkey"
```

El archivo `.env` contiene la URL de conexión completa a la base de datos de Supabase en producción, incluyendo contraseña en texto plano. Si este archivo está rastreado por git (lo cual es probable dado que el agente lo encontró), las credenciales están en el historial de commits y deben considerarse **comprometidas permanentemente**, incluso después de rotar.

**Acciones inmediatas:**
1. Rotar la contraseña de la base de datos Supabase ahora.
2. Rotar `SECRET_KEY` JWT.
3. Añadir `.env` a `.gitignore` si no está ya.
4. Usar `git filter-branch` o `git-filter-repo` para purgar el historial.
5. Para CI/CD y producción, usar variables de entorno del sistema o un gestor de secretos (Render.com, Railway, etc. tienen esto nativo).

---

### A-01 — Alto · Bug / Datos: Pago sin transacción atómica

**Archivo:** `app/routers/collect_debts.py:161-264`

La operación de registro de pago realiza múltiples escrituras en secuencia:

```python
db.add(db_payment)
db.flush()  # obtiene ID

for item in debt_items:
    # actualiza DebtItem.balance, DebtItem.status
    # crea PaymentDetail
    db.add(payment_detail)

# actualiza CollectDebt.total_collected
db.commit()  # único commit al final
```

El `flush()` seguido de lógica de negocio antes del `commit()` es correcto en principio, pero si ocurre una excepción en medio del loop (e.g., `debt_item` no encontrado, error de red), el commit nunca se ejecuta y la sesión queda en estado inconsistente. El `get_db()` dependency hace `db.close()` en el `finally` pero **no hace rollback explícito**. SQLAlchemy puede o no hacer rollback automático dependiendo de la versión y configuración.

**Fix:**
```python
# app/dependencies.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

Y en operaciones complejas, usar context manager explícito:
```python
try:
    # ... lógica de pago
    db.commit()
except Exception:
    db.rollback()
    raise HTTPException(status_code=500, detail="Payment processing failed")
```

---

### A-02 — Alto · Bug: Balance negativo no validado en pagos

**Archivo:** `app/routers/collect_debts.py:213`

```python
new_balance = previous_balance - amount_applied
# No hay validación de que amount_applied <= previous_balance
```

Un `amount_applied` mayor que `previous_balance` resulta en balance negativo. Esto:
- Marca la deuda como pagada (`status = "paid"`)
- Registra un balance negativo en `PaymentDetail.new_balance`
- Hace que `collect_debt.total_collected` registre un monto mayor al real

**Fix:**
```python
if amount_applied <= 0:
    raise HTTPException(status_code=400, detail=f"amount_applied must be positive for debt {debt_item_id}")
if amount_applied > previous_balance:
    raise HTTPException(status_code=400, detail=f"amount_applied exceeds balance for debt {debt_item_id}")
```

---

### A-03 — Alto · Bug: Cálculo de consumo de agua usa `id` en lugar de fecha

**Archivo:** `app/routers/measures.py:214-217`

```python
previous_reading = db.query(models.MeterReading).filter(
    models.MeterReading.meter_id == reading.meter_id,
    models.MeterReading.id < reading.id  # ← Orden por ID, no por fecha
).order_by(models.MeterReading.id.desc()).first()
```

Si las lecturas se ingresan fuera de orden cronológico (corrección retroactiva, re-ingreso de datos), el `id` menor no corresponde a la lectura cronológicamente anterior. Esto puede producir consumos negativos (lectura actual < lectura "anterior" por ID) o consumos inflados. Para un sistema de facturación de agua esto es un error de alto impacto.

**Fix:**
```python
previous_reading = db.query(models.MeterReading).filter(
    models.MeterReading.meter_id == reading.meter_id,
    models.MeterReading.reading_date < reading.reading_date
).order_by(models.MeterReading.reading_date.desc()).first()
```

También agregar validación de `consumption < 0` antes de generar la deuda.

---

### A-04 — Alto · Bug: Referencias a modelos inexistentes en CRUD

**Archivo:** `app/services/crud.py:50-58` y `app/routers/neighbors.py:35-53`

```python
# crud.py
def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()  # models.Item no existe

def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.model_dump(), owner_id=user_id)  # models.Item no existe
```

```python
# neighbors.py
@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)  # crud.get_user no existe
```

`models.Item` y `crud.get_user` no están definidos en ningún lugar del proyecto. Estas rutas causan `AttributeError` en runtime. Son remanentes de código scaffolding que nunca fueron limpiados.

**Fix:** Eliminar `get_items`, `create_user_item` de `crud.py`, y los endpoints `/users/{user_id}`, `/users/{user_id}/items/`, `/items/` de `neighbors.py`.

---

### A-05 — Alto · Bug: `POST /{collect_debt_id}/payments` usa query params para payload complejo

**Archivo:** `app/routers/collect_debts.py:161-172`

```python
@router.post("/{collect_debt_id}/payments")
def create_collect_debt_payment(
  collect_debt_id: int,
  neighbor_id: int,           # ← Query param
  total_amount: float,        # ← Query param
  payment_method: str = None, # ← Query param
  debt_items: list[dict] = None,  # ← list[dict] como query param — inviable
  db: Session = Depends(get_db)
):
```

FastAPI no puede deserializar `list[dict]` desde query parameters. En la práctica, `debt_items` siempre llega como `None`. Esto significa que los detalles de pago (qué deudas se están pagando) **nunca se registran**, los balances de deuda **nunca se actualizan**, y los `PaymentDetail` records **nunca se crean** — aunque el `Payment` sí se crea.

**Fix:** Crear un schema Pydantic para el body del request:
```python
class PaymentItemInput(BaseModel):
    debt_item_id: int
    amount_applied: float

class CreatePaymentRequest(BaseModel):
    neighbor_id: int
    total_amount: float
    payment_method: str | None = None
    reference_number: str | None = None
    received_by: str | None = None
    notes: str | None = None
    debt_items: list[PaymentItemInput] = []

@router.post("/{collect_debt_id}/payments")
def create_collect_debt_payment(
    collect_debt_id: int,
    payload: CreatePaymentRequest,  # Body JSON
    db: Session = Depends(get_db)
):
```

---

### M-01 — Medio · Performance: Paginación ignorada en `get_neighbors()`

**Archivo:** `app/services/crud.py:18-20`

```python
def get_neighbors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Neighbor).all()
    #       .offset(skip).limit(limit)  ← comentado
```

La paginación está comentada. Con una comunidad de cientos de vecinos, más sus relaciones lazy-loaded (medidores, deudas, asistencias), esto puede producir queries lentas y respuestas de varios MB.

**Fix:** Descomentar `.offset(skip).limit(limit)`, y considerar añadir también un `order_by` determinista para resultados estables.

---

### M-02 — Medio · Calidad: Duplicación masiva de serialización de respuestas

Prácticamente cada endpoint construye manualmente un dict para la respuesta:

```python
# Esto se repite ~20 veces en el proyecto:
return {
    "id": db_meet.id,
    "meet_date": str(db_meet.meet_date),
    "meet_type": db_meet.meet_type,
    "title": db_meet.title,
    # ... 15 campos más
}
```

Y al mismo tiempo se declara `response_model=schemas.Meet`, que tiene exactamente esos campos. Hay dos problemas:
1. **Violación DRY**: cada cambio en el modelo requiere actualizar 3-4 lugares (model + schema + cada endpoint que serializa).
2. **`response_model` ignorado**: el dict manual bypass el schema de validación de salida de Pydantic.

**Fix:** Usar `model_validate` o configurar `from_attributes = True` (ya está en algunos schemas) y retornar directamente el objeto ORM:

```python
# En lugar de construir el dict manualmente:
@router.get("/{measure_id}", response_model=schemas.Measure)
def read_measure(measure_id: int, db: Session = Depends(get_db)):
    measure = crud.get_measure(db, measure_id=measure_id)
    if measure is None:
        raise HTTPException(status_code=404, detail="Measure not found")
    return measure  # FastAPI + Pydantic serializa automáticamente
```

El problema con las fechas (no son strings en el ORM) se resuelve usando `datetime` en los schemas en lugar de `str`.

---

### M-03 — Medio · Calidad: Fechas como `str` en schemas Pydantic

**Archivo:** `app/schemas/schema.py` (múltiples clases)

```python
class MeasureBase(BaseModel):
    measure_date: str  # "Fecha en formato string"
```

Usar `str` para fechas descarta toda la validación de Pydantic. Un cliente puede enviar `"mañana"`, `"31/02/2024"` o `""` y el schema lo acepta. La conversión manual con `strptime` en `crud.py` no maneja errores:

```python
# crud.py:137 — Sin try/except
measure_date = datetime.strptime(measure.measure_date, "%Y-%m-%d").date()
# ValueError si el formato es incorrecto → HTTP 500
```

**Fix:**
```python
from datetime import date, datetime
from pydantic import field_validator

class MeasureBase(BaseModel):
    measure_date: date  # Pydantic valida y parsea automáticamente
```

Esto elimina el `strptime` manual en `crud.py`, centraliza la validación, y retorna 422 con mensaje claro al cliente en lugar de 500.

---

### M-04 — Medio · Arquitectura (SRP): Lógica de negocio en routers

**Archivos:** `app/routers/measures.py:168-265`, `app/routers/collect_debts.py:161-264`

Los routers contienen lógica de negocio sustancial: cálculo de consumo de agua, generación de deudas, aplicación de pagos, actualización de estadísticas. Esto viola el principio de responsabilidad única:

- Los routers deberían limitarse a parsear requests y delegar.
- La lógica de negocio (ej: `consumption <= 20 → Bs. 20`) debería estar en una capa de servicios, testeable de forma aislada.

El resultado actual: lógica de facturación imposible de testear sin instanciar una sesión de DB y simular HTTP requests.

**Estructura recomendada:**
```
app/
  services/
    crud.py          # operaciones CRUD puras
    payment_service.py   # lógica de pagos
    billing_service.py   # lógica de facturación de agua
    stats_service.py     # recálculo de estadísticas
```

---

### M-05 — Medio · Bug: Respuesta inconsistente cuando no hay vecinos

**Archivo:** `app/routers/neighbors.py:27-33`

```python
if neighbors:
    return {"data": neighbors, "total": len(neighbors), ...}
return {'success': 'True'}  # ← Retorna un objeto distinto para lista vacía
```

Una lista vacía (`[]`) es falsy en Python, por lo que cuando no hay vecinos el endpoint retorna `{'success': 'True'}` en lugar de `{"data": [], "total": 0, ...}`. El frontend recibe un tipo de respuesta diferente según si hay datos o no, lo que obliga a manejar dos formatos distintos.

**Fix:**
```python
return {
    "data": neighbors,
    "total": len(neighbors),
    "page": skip // limit + 1 if limit > 0 else 1,
    "size": limit
}
```

---

### M-06 — Medio · Arquitectura: Trailing slash inconsistente en rutas

**Archivo:** `app/routers/meets.py:81`

```python
@router.post("/", response_model=schemas.Meet)   # POST /meets/ (con slash)
def create_meet(meet: schemas.MeetCreate, ...):

@router.get("")                                   # GET /meets (sin slash)
def read_meets(...):
```

FastAPI por defecto no redirige `/meets` a `/meets/`. Un cliente que haga `POST /meets` (sin slash) recibirá 307 o 404 dependiendo de la configuración. El resto de routers usa `""` sin slash. Inconsistencia que causa bugs difíciles de detectar en producción.

**Fix:** Usar `""` (sin trailing slash) en todos los endpoints de creación, consistente con el resto del proyecto.

---

### M-07 — Medio · Seguridad: `SECRET_KEY` predecible

**Archivo:** `.env:9`

```
SECRET_KEY = "supersecretkey"
```

Además del issue C-01, incluso si se corrigiera el bug del JWT, esta clave es extremadamente débil. Aparece en listas de contraseñas comunes y es trivialmente bruteforceable con herramientas como `hashcat` sobre JWTs capturados.

**Fix:** Generar una clave criptográficamente segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Mínimo 256 bits de entropía para HS256.

---

### B-01 — Bajo · Testing: Sin suite de tests

El directorio `test/` está vacío. Los únicos "tests" son scripts utilitarios en la raíz (`users.py`, `database_test_alchemy.py`, `test_direct.py`, `test_update.py`) que son scripts de exploración ad-hoc, no tests automatizados con asserts.

Con lógica financiera crítica (cálculo de consumo, aplicación de pagos, generación de deudas), la ausencia de tests representa un riesgo operativo elevado.

**Quick wins prioritarios para testing:**
1. Tests unitarios de `verify_password()` y `create_access_token()`
2. Tests de integración para el flujo de pago completo (create payment → verify balances updated)
3. Tests del cálculo de consumo de agua con casos edge (consumo negativo, primer registro)

**Stack recomendado:** `pytest` + `pytest-asyncio` + `httpx.AsyncClient` + SQLite en memoria para tests de integración rápidos.

---

### B-02 — Bajo · Calidad: `import` dentro de funciones

**Archivo:** `app/services/crud.py` (múltiples funciones: líneas 134, 207, 233, etc.)

```python
def create_measure(db: Session, measure: schemas.MeasureCreate):
    from datetime import datetime  # ← Import dentro de función
    measure_date = datetime.strptime(...)
```

Los imports dentro de funciones se re-evalúan en cada llamada (aunque Python cachea módulos, el lookup tiene overhead). Más importante, oscurece las dependencias del módulo y dificulta el análisis estático. Mover todos al top del archivo.

---

### B-03 — Bajo · Calidad: Comentario desactualizado en schema

**Archivo:** `app/schemas/schema.py:87-89`

```python
amount: int  # Monto total en centavos
amount_paid: int  # Monto ya pagado
balance: int  # Saldo pendiente
```

El comentario "en centavos" es incorrecto post-migración a bolivianos (el endpoint de migración existe precisamente para convertir de centavos a bolivianos). El esquema también usa `int` para montos monetarios cuando los valores actuales son `float` (división por 100 en la migración). Esto produce truncamiento silencioso.

**Fix:** Actualizar comentarios, cambiar a `float` o `Decimal` para valores monetarios.

---

### B-04 — Bajo · DevOps: Sin gestión de migraciones

**Archivo:** `app/main.py:18`

```python
Base.metadata.create_all(bind=engine)
```

`create_all()` en startup solo crea tablas nuevas — no altera las existentes. Cualquier cambio de schema (añadir columna, cambiar tipo) en producción requiere intervención manual o causa inconsistencias silenciosas.

**Fix:** Integrar Alembic:
```bash
pip install alembic
alembic init alembic
# Generar migraciones con: alembic revision --autogenerate -m "description"
# Aplicar con: alembic upgrade head
```

---

### B-05 — Bajo · Calidad: Typo en tag del router

**Archivo:** `app/routers/debts.py:11`

```python
router = APIRouter(
    prefix="/debts",
    tags=['Dets'],  # ← Debería ser 'Debts'
)
```

Esto afecta la documentación OpenAPI generada automáticamente por FastAPI.

---

## Quick Wins (prioridad inmediata antes de producción)

Estos cambios son < 30 min cada uno y eliminan los riesgos más críticos:

1. **[C-01]** `main.py:49` — cambiar `settings.ALGORITHM` por `settings.SECRET_KEY` en `jwt.encode`.
2. **[C-02]** `models/user.py:17` — reemplazar `bcrypt.hashpw(...)` con `bcrypt.checkpw(...)`.
3. **[C-03]** Añadir `Depends(get_current_user)` en todos los routers de negocio.
4. **[C-04]** Remover el endpoint `/debts/migrate-to-bolivianos` del código fuente.
5. **[C-05]** Rotar credenciales de DB y JWT secret. Agregar `.env` a `.gitignore`.
6. **[A-05]** Mover params de `POST /payments` a body JSON con schema Pydantic.
7. **[M-05]** Retornar siempre el mismo shape en `read_neighbors`.

---

## Mejoras Estructurales (sprint 1-2)

Requieren más esfuerzo pero son necesarias antes de escalar:

1. **Capa de servicios**: extraer lógica de negocio de los routers a `services/billing_service.py` y `services/payment_service.py`.
2. **Tipos nativos en schemas**: migrar fechas de `str` a `date`/`datetime` en Pydantic. Elimina 40+ líneas de `strptime` manual.
3. **Serialización con `response_model`**: retornar objetos ORM directamente, eliminar los ~500 líneas de serialización manual.
4. **Rollback explícito en `get_db()`**: añadir `except/rollback` al dependency.
5. **Alembic**: reemplazar `create_all()` con migraciones versionadas.
6. **Tests**: pytest + httpx con BD SQLite en memoria. Empezar por el flujo de pagos.

---

## Detección de Patrones AI-Generated

El código presenta señales características de generación asistida por IA:
- Comentarios docstring exhaustivos en funciones CRUD sencillas (`"""Obtiene todas las recaudaciones ordenadas por fecha de creación (más recientes primero)"""`) en un nivel de detalle inusual para código interno.
- Bloques de serialización manual repetitivos con estructura idéntica (típico de "generate similar endpoint").
- Los bugs más críticos (C-01: key vs algorithm, C-02: hashpw vs checkpw) son errores de "parece correcto a primera vista" consistentes con código generado sin ejecución de tests.
- `import datetime` dentro de cada función en lugar de al inicio del módulo.

**Riesgo asociado:** El código generado por IA tiende a producir código que _parece_ correcto sintácticamente pero introduce bugs sutiles en lógica de seguridad. La ausencia de tests amplifica este riesgo. La recomendación es no asumir corrección en ninguna operación de seguridad/financiera sin test de integración que lo valide end-to-end.

---

*Fin del informe. Los hallazgos C-01 a C-05 deben resolverse antes de cualquier despliegue a producción.*
