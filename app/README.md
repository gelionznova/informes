# Generador de Informes (Local)

Aplicacion local para diligenciar datos y generar:

- INF. GESTION
- INF. SUPERVISION
- ACTA PARCIAL

Estructura:

- app.py: servidor Flask.
- db.py: acceso a SQLite.
- services/docx_generator.py: render de plantillas.
- templates/: interfaz HTML.
- static/: estilos.
- docx_templates/: plantillas .docx con placeholders.
- output/: documentos generados.
- data/: base SQLite local.

Requisitos:

- Python 3.11 (para empaquetar).
- Windows 10/11.

Ejecucion local (modo desarrollo):

1. Crear entorno virtual.
2. Instalar dependencias desde requirements.txt.
3. Ejecutar app.py.
4. Abrir el navegador en http://127.0.0.1:5050.

Autenticacion:

- Usuario inicial: admin
- Clave inicial: admin123
- Rol inicial: super_admin

Desde el panel de administracion puedes crear roles y usuarios, y asignar roles.

Empaquetar a .exe (PyInstaller):

1. Crear un entorno con Python 3.11.
2. Instalar dependencias y PyInstaller.
3. Ejecutar el build desde la carpeta informe:

py -3.11 -m venv .venv_clean311
.\.venv_clean311\Scripts\python.exe -m pip install -r app\requirements.txt
.\.venv_clean311\Scripts\python.exe -m pip install pyinstaller
.\.venv_clean311\Scripts\python.exe -m PyInstaller --clean --noconfirm --log-level=INFO --onefile --add-data "app\templates;templates" --add-data "app\static;static" --add-data "app\docx_templates;docx_templates" --add-data "app\data;data" app\app.py

El ejecutable queda en dist\app.exe.

Uso del ejecutable:

1. Abrir dist\app.exe.
2. Completar el formulario y generar documentos.
3. Los .docx se guardan en app\output.

Placeholders usados en las plantillas .docx:

- Datos generales:
  - {{informe_no}}
  - {{contrato_no}}
  - {{fecha_contrato}}
  - {{objeto_contractual}}
  - {{entidad_contratante}}
  - {{nit}}
  - {{contratista}}
  - {{cc}}
  - {{ciudad_expedicion}}
  - {{plazo_dia}}
  - {{plazo_mes}}
  - {{plazo_anio}}
  - {{fecha_inicio_contrato}}
  - {{fecha_vencimiento_contrato}}
  - {{valor_inicial}}
  - {{cdp}}
  - {{rp}}
  - {{periodo_i_de}}
  - {{periodo_i_a}}
  - {{fecha_expedicion_informe_dia}}
  - {{fecha_expedicion_informe_mes}}
  - {{fecha_expedicion_informe_año}}
  - {{fecha_presentacion_informe}}

- Obligaciones directas:
  - {{obligaciones_directas}}
  - {{obligaciones_directas_ejecutadas}}
  - {{aporta_evidencias}} (en tabla, por fila)

- Obligaciones generales:
  - {{obligaciones_generales}}
  - {{obligaciones_generales_ejecutadas}}

- Seguridad social:
  - {{aportes_planilla}}
  - {{aportes_mes}}
  - {{fecha_pago_aportes}}
  - {{operador_planilla}}
  - {{aportes_valor_salud}}
  - {{aportes_valor_pension}}
  - {{aportes_valor_riesgos}}
  - {{total_aportes}}

- Informacion financiera:
  - {{valor_contrato}}
  - {{valor_anticipo}}
  - {{valor_pago_anticipado}}
  - {{valor_adiciones}}
  - {{valor_ejecutado}}
  - {{valor_a_cobrar}}
  - {{saldo_pendiente}}
  - {{valor_presente_informe}}
  - {{actas_subtotal}}

- Actas parciales (tabla):
  - {{actas_parciales}} (lista de objetos con: acta, periodo, valor)
