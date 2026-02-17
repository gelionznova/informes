# Generador de Informes (Local)

Aplicación local en Flask para diligenciar información contractual, generar documentos Word y gestionar revisión por supervisor.

## Documentos que genera

- `INF. GESTION.docx`
- `INF.SUPERVISION.docx`
- `ACTA.docx`
- `ANEXO.docx`

Los archivos se guardan en `app/output/` con prefijo del consecutivo (`00001_...`, `00002_...`, etc.).

## Funcionalidades principales

- Inicio de sesión con roles (`super_admin`, `supervisor`, `contratista`, `por_asignar`).
- Formulario web para captura de datos del informe.
- Generación de documentos DOCX con plantillas en `app/docx_templates/`.
- Historial de envíos en SQLite (`app/data/app.db`).
- Panel de supervisión (listar, revisar, aprobar/rechazar informes).
- Panel de administración para gestión de roles y usuarios.

## Requisitos

- Python 3.11 recomendado
- Windows 10/11

Dependencias (`requirements.txt`):

- Flask 3.0.0
- docxtpl 0.17.0
- python-docx 1.1.2

## Ejecución local (desarrollo)

Desde la carpeta `app`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

La app inicia en `http://127.0.0.1:5050`.

Al iniciar por primera vez, se crean base de datos, roles por defecto y usuario administrador inicial.

## Usuario inicial

- Usuario: `admin`
- Clave: `admin123`
- Rol: `super_admin`

> Recomendado: cambiar la clave inmediatamente en ambiente real.

## Variables de entorno

- `APP_SECRET_KEY`: clave de sesión Flask (si no se define, usa `change-this-secret`).
- `FLASK_DEBUG=1`: activa modo debug y desactiva apertura automática del navegador.

## Estructura del módulo `app/`

- `app.py`: servidor Flask, rutas web/API, autenticación y reglas de negocio.
- `db.py`: inicialización SQLite y operaciones CRUD de usuarios, roles y submissions.
- `services/docx_generator.py`: renderizado de plantillas DOCX y armado de anexo con evidencias.
- `templates/`: vistas HTML (`login`, `index`, `admin`).
- `static/`: estilos y scripts frontend.
- `docx_templates/`: plantillas fuente de Word.
- `output/`: documentos generados.
- `data/`: base local (`app.db`).

## Endpoints principales

### Web

- `GET /` formulario principal (requiere login)
- `GET|POST /login`
- `GET /logout`
- `GET /admin` panel de administración (solo `super_admin`)

### Generación e historial

- `POST /generate` genera documentos y guarda envío
- `GET /history`
- `GET /history/<record_id>`
- `POST /history/<record_id>/delete`
- `GET /download/<record_id>/<doc_key>`

### Supervisor (API)

- `GET /api/supervisor/reports`
- `GET /api/supervisor/report/<record_id>`
- `POST /api/supervisor/report/<record_id>/review`

## Plantillas y placeholders

Las plantillas DOCX usan placeholders Jinja (`{{ campo }}`).

## Variables de contexto (`POST /generate`)

Estas son las variables que la app espera en el payload para renderizar plantillas y completar tablas dinámicas.

### Datos generales

- `informe_no`
- `contrato_no`
- `fecha_contrato`
- `objeto_contractual`
- `entidad_contratante`
- `nit`
- `contratista`
- `supervisor`
- `supervisor_cc`
- `cc`
- `ciudad_expedicion`
- `plazo_dia`
- `plazo_mes`
- `plazo_anio`
- `fecha_inicio_contrato`
- `fecha_vencimiento_contrato`
- `valor_inicial`
- `cdp`
- `rp`
- `periodo_i_de`
- `periodo_i_a`
- `fecha_expedicion_informe_dia`
- `fecha_expedicion_informe_mes`
- `fecha_expedicion_informe_año`
- `fecha_presentacion_informe`

### Obligaciones

- `obligaciones_directas`
- `obligaciones_directas_ejecutadas`
- `obligaciones_generales`
- `obligaciones_generales_ejecutadas`

Para tablas dinámicas por actividad:

- `obligaciones_directas_items`: lista de objetos con:
  - `actividad_contrato`
  - `actividad_ejecutada`
  - `aporta_evidencias`
  - `evidencias` (opcional, usado por `ANEXO.docx`)

Estructura de `evidencias`:

- `images`: lista de imágenes base64 (`dataUrl` o `data_url`)
- `groups`: lista de metadatos por bloque (máx. 3 imágenes por bloque):
  - `description`
  - `date`

### Seguridad social

- `aportes_planilla`
- `aportes_mes`
- `fecha_pago_aportes`
- `operador_planilla`
- `aportes_valor_salud`
- `aportes_valor_pension`
- `aportes_valor_riesgos`
- `total_aportes` (si falta, la app intenta calcularlo automáticamente)

### Información financiera

- `valor_contrato`
- `valor_anticipo`
- `valor_pago_anticipado`
- `valor_adiciones`
- `valor_ejecutado`
- `valor_a_cobrar`
- `saldo_pendiente`
- `valor_presente_informe`
- `actas_subtotal`

### Actas parciales

- `actas_parciales`: lista de objetos con:
  - `acta`
  - `periodo`
  - `valor`

### Campos derivados internamente

No se deben enviar obligatoriamente; la app los construye cuando aplica:

- `obligaciones_directas_ejecutadas_tercera`
- `obligaciones_directas_items_tercera`

Script de validación disponible:

```powershell
python _validate_placeholders.py
```

Script de generación de prueba:

```powershell
python _test_generate.py
```

## Empaquetado a ejecutable (.exe)

Desde la raíz del proyecto (`informe/`):

```powershell
py -3.11 -m venv .venv_clean311
.\.venv_clean311\Scripts\python.exe -m pip install -r app\requirements.txt
.\.venv_clean311\Scripts\python.exe -m pip install pyinstaller
.\.venv_clean311\Scripts\python.exe -m PyInstaller --clean --noconfirm --log-level=INFO --onefile --add-data "app\templates;templates" --add-data "app\static;static" --add-data "app\docx_templates;docx_templates" --add-data "app\data;data" app\app.py
```

Salida esperada: `dist/app.exe`.

## Notas operativas

- La app autocalcula `total_aportes` cuando no se envía y existen valores de salud/pensión/riesgos.
- En informes de supervisión se genera versión en tercera persona para actividades ejecutadas.
- Si `FLASK_DEBUG` no está activo, la app intenta abrir el navegador automáticamente al arrancar.
