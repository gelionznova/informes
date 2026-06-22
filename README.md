# Informes

Aplicacion local para generar y administrar informes contractuales.

## Resumen

Informes es una app de escritorio/web local construida con Flask para registrar informacion contractual, generar documentos Word y gestionar el flujo de revision por usuarios autorizados.

## Funciones principales

- Inicio de sesion con roles de administrador, supervisor y contratista.
- Captura de datos para informes contractuales.
- Generacion de documentos DOCX desde plantillas.
- Historial local en SQLite.
- Panel de administracion para usuarios, roles y configuracion operativa.
- Flujo de supervision para revisar, aprobar o rechazar informes.
- Construccion de ejecutable Windows con PyInstaller.

## Ejecutable

El ejecutable generado queda en:

```text
dist/GenInfo.exe
```

## Desarrollo local

```powershell
cd app
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

La app inicia en:

```text
http://127.0.0.1:5050
```

## Usuario inicial

```text
Usuario: admin
Clave: admin123
```

Se recomienda cambiar la clave inicial antes de usar la app en un entorno real.
