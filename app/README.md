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
- Autoguardado de progreso del formulario (incluye pestaña activa y recuperación automática por usuario).
- Generación de documentos DOCX con plantillas en `app/docx_templates/`.
- Historial de envíos en SQLite.
  - Desarrollo: `app/data/app.db`
  - Ejecutable `.exe`: `%LOCALAPPDATA%\\GeneradorInformes\\data\\app.db`
- Panel de supervisión (listar, revisar, aprobar/rechazar informes).
- Panel de administración para gestión de roles y usuarios.
- Exportación e importación de base de datos desde el panel de administración.
- Respaldo automático previo a cada importación en `%LOCALAPPDATA%\\GeneradorInformes\\backups`.
- Respaldo personal para `contratista` (exportar/importar solo sus propios registros en JSON).

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
- `GET /admin/database/export` exporta la base SQLite actual
- `POST /admin/database/import` importa una SQLite y reemplaza la actual (con backup previo)
- `GET /contractor/history/export` exporta respaldo JSON del historial propio del contratista
- `POST /contractor/history/import` importa respaldo JSON del historial propio del contratista

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
- `pdfs`: lista de archivos PDF en base64 (`name`, `dataUrl`)
- `links`: lista de enlaces (URLs) para generar QR en `ANEXO.docx`
- `link`: compatibilidad con versiones anteriores (primer enlace)

### Seguridad social

- `aportes_planilla`
- `aportes_mes`
- `fecha_pago_aportes`
- `operador_planilla`
- `aportes_valor_salud`
- `aportes_valor_pension`
- `aportes_valor_riesgos`
- `aportes_valor_caja_compensacion_familiar`
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

## Respaldos y actualización segura

### Flujo recomendado antes de actualizar

1. En la versión actual, entrar como `super_admin` al panel **Base de datos**.
2. Usar **Exportar base de datos** y guardar el archivo `.db` en una ubicación segura.
3. Instalar o abrir la nueva versión del `.exe`.
4. En la nueva versión, usar **Importar base de datos** con el archivo exportado.

### Buenas prácticas técnicas

- Mantener la base de datos fuera del ejecutable (ya se usa `%LOCALAPPDATA%\\GeneradorInformes\\data\\app.db`).
- Versionar esquema con `PRAGMA user_version` y aplicar migraciones incrementales en `init_db()`.
- Nunca eliminar columnas/tablas en una actualización sin estrategia de migración reversible.
- Crear backup automático antes de operaciones críticas (ya implementado para import).
- Para cambios grandes de esquema, usar migraciones idempotentes y pruebas con copia real de datos.

### Notas de migraciones

- La app ejecuta `SCHEMA_SQL` y normalizaciones de columnas en cada arranque.
- Si agregas una nueva migración, incrementa versión y aplica `ALTER TABLE`/transformaciones de forma segura.
- Evita resets de datos por código de inicialización; el seed debe usarse solo para primera ejecución.

Salida esperada: `dist/app.exe`.

### Script automatizado (build + firma opcional)

También puedes usar el script de la raíz del proyecto:

```powershell
.\scripts\build-and-sign.ps1
```

Con firma digital (selección automática de certificado):

```powershell
.\scripts\build-and-sign.ps1 -Sign
```

Con huella específica de certificado:

```powershell
.\scripts\build-and-sign.ps1 -Sign -CertificateThumbprint "TU_HUELLA_SHA1"
```

## Solución de problemas frecuentes

### Error en consola: `Invalid Unicode escape sequence` y `userRole is not defined`

Si aparece en algunos equipos al abrir la app, normalmente es por JavaScript cacheado por el navegador.

Pasos:

1. Cerrar la app.
2. Limpiar caché del navegador usado por la app (`Ctrl+Shift+R` o borrar datos del sitio).
3. Volver a abrir el ejecutable actualizado.

Notas:

- `userRole is not defined` suele ser un error en cascada cuando el script se corta antes por un `SyntaxError`.
- Si persiste, abrir DevTools y recargar forzado para confirmar que el archivo JS nuevo quedó aplicado.

### Mensaje Windows: "No se puede ejecutar esta aplicación en el equipo"

Causas más comunes:

- Arquitectura incompatible (ejecutable x64 en Windows x86).
- Ejecutable incompleto/corrupto al copiar o descargar.

Checklist de validación:

1. Verificar arquitectura del equipo destino (`Configuración > Sistema > Acerca de > Tipo de sistema`).
2. Construir el `.exe` con Python de la misma arquitectura del destino.
3. Copiar de nuevo el archivo completo (mejor en `.zip`) y reintentar.
4. Si está en red/correo, probar desbloquear archivo (`Propiedades > Desbloquear`).

Recomendación práctica de distribución:

- Publicar dos builds: `app-x64.exe` y `app-x86.exe` (si aún tienes equipos x86).
- Firmar ambos ejecutables para reducir bloqueos por seguridad.

## Aviso de Windows SmartScreen ("Windows protegió su PC")

Es normal que aparezca en algunos equipos cuando el ejecutable no está firmado o no tiene reputación suficiente en Microsoft Defender SmartScreen.

Esto puede variar entre equipos por políticas de seguridad, versión de Windows/Defender y origen del archivo (por ejemplo, descargado desde internet o copiado desde red).

### Recomendación para producción

Firmar `dist/app.exe` con un certificado de firma de código para que Windows pueda identificar al editor.

Pasos generales:

1. Obtener un certificado de firma de código (OV o EV) de una entidad certificadora.
2. Instalar el certificado en Windows (almacén `Personal` del usuario o del equipo que firma).
3. Firmar el ejecutable con `signtool`.
4. Verificar la firma antes de distribuir.

Ejemplo con `signtool`:

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\app.exe
signtool verify /pa /v dist\app.exe
```

Notas:

- EV suele obtener reputación más rápido en SmartScreen.
- Si se recompila el `.exe` continuamente, cada binario cambia y puede volver a aparecer la advertencia hasta consolidar reputación.
- En ambientes corporativos, también se puede permitir el ejecutable por políticas (GPO/Intune/Defender).

## Notas operativas

- La app autocalcula `total_aportes` cuando no se envía y existen valores de salud/pensión/riesgos/caja de compensación familiar.
- En informes de supervisión se genera versión en tercera persona para actividades ejecutadas.
- Si `FLASK_DEBUG` no está activo, la app intenta abrir el navegador automáticamente al arrancar.
