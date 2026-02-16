# --- ENDPOINTS SUPERVISOR ---
from datetime import datetime




import os
import re
import sys
import threading
import webbrowser
from functools import wraps
import secrets
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    url_for,
    redirect,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash

from db import (
    init_db,
    save_submission,
    list_submissions,
    get_submission,
    delete_submission,
    list_roles,
    get_role_by_name,
    get_role_by_id,
    create_role,
    update_role,
    delete_role,
    reassign_users_role,
    list_users,
    get_user_by_username,
    create_user,
    update_user_role,
    update_user,
    delete_user,
    has_any_users,
    get_user_by_id,
    list_users_by_role,
)
from services.docx_generator import generate_documents, TEMPLATE_FILES, OUTPUT_DIR

def _resource_path(*parts: str) -> str:
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, *parts)

app = Flask(
    __name__,
    template_folder=_resource_path("templates"),
    static_folder=_resource_path("static"),
    static_url_path="/static",
)
app.secret_key = os.environ.get("APP_SECRET_KEY", "change-this-secret")
APP_BOOT_ID = secrets.token_hex(8)

ROLE_SUPER_ADMIN = "super_admin"
ROLE_SUPERVISOR = "supervisor"
ROLE_CONTRATISTA = "contratista"
ROLE_POR_ASIGNAR = "por_asignar"
DOC_TYPES = [
    {"value": "cedula_ciudadania", "label": "Cedula de ciudadania"},
    {"value": "cedula_extranjeria", "label": "Cedula de extranjeria"},
    {"value": "pasaporte", "label": "Pasaporte"},
    {"value": "nit", "label": "NIT"},
]

def _get_tab_id() -> str | None:
    return request.headers.get("X-Tab-Id") or request.values.get("tab_id")

def _append_tab_id(url: str, tab_id: str | None) -> str:
    if not tab_id:
        return url
    try:
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query))
        query["tab_id"] = tab_id
        return urlunparse(parsed._replace(query=urlencode(query)))
    except ValueError:
        return url

def _get_tab_user(tab_id: str) -> dict | None:
    tabs = session.get("tabs")
    if not isinstance(tabs, dict):
        return None
    return tabs.get(tab_id)

def _current_user() -> dict | None:
    if session.get("boot_id") != APP_BOOT_ID:
        session.clear()
        return None
    tab_id = _get_tab_id()
    if tab_id:
        user = _get_tab_user(tab_id)
        if not user:
            return None
        return user
    if not session.get("user_id"):
        return None
    return {
        "id": session.get("user_id"),
        "username": session.get("username"),
        "role": session.get("role"),
    }

def _wants_json() -> bool:
    return request.path.startswith("/history") or request.path.startswith("/generate") or request.path.startswith("/download")

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _current_user():
            if _wants_json():
                return jsonify({"ok": False, "error": "auth_required"}), 401
            tab_id = _get_tab_id()
            return redirect(_append_tab_id(url_for("login", next=request.path), tab_id))
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = _current_user()
        if not user:
            tab_id = _get_tab_id()
            return redirect(_append_tab_id(url_for("login", next=request.path), tab_id))
        if user.get("role") != ROLE_SUPER_ADMIN:
            return jsonify({"ok": False, "error": "forbidden"}), 403
        return func(*args, **kwargs)
    return wrapper

def _ensure_default_roles_and_admin() -> None:
    for role_name in (
        ROLE_SUPER_ADMIN,
        ROLE_SUPERVISOR,
        ROLE_CONTRATISTA,
        ROLE_POR_ASIGNAR,
    ):
        if not get_role_by_name(role_name):
            create_role(role_name)
    if not has_any_users():
        role = get_role_by_name(ROLE_SUPER_ADMIN)
        if role:
            password_hash = generate_password_hash("admin123")
            create_user(
                "admin",
                password_hash,
                role["id"],
                "Admin",
                "Principal",
                "cedula_ciudadania",
                "0000000000",
            )
        (r"aprob[éeo]\b", "aprobó"),
        (r"archiv[éeo]\b", "archivó"),
        (r"asesor[éeo]\b", "asesoró"),
        (r"capacit[éeo]\b", "capacitó"),
        (r"certific[éeo]\b", "certificó"),
        (r"comunic[éeo]\b", "comunicó"),
        (r"consolid[éeo]\b", "consolidó"),
        (r"control[éeo]\b", "controló"),
        (r"correspond[íio]\b", "correspondió"),
        (r"custodi[éeo]\b", "custodió"),
        (r"digitaliz[éeo]\b", "digitalizó"),
        (r"diligenci[éeo]\b", "diligenció"),
        (r"elimin[éeo]\b", "eliminó"),
        (r"emit[íio]\b", "emitió"),
        (r"evalu[éeo]\b", "evaluó"),
        (r"exped[íio]\b", "expidió"),
        (r"facilit[éeo]\b", "facilitó"),
        (r"formaliz[éeo]\b", "formalizó"),
        (r"inform[éeo]\b", "informó"),
        (r"inspeccion[éeo]\b", "inspeccionó"),
        (r"instal[éeo]\b", "instaló"),
        (r"integr[éeo]\b", "integró"),
        (r"inventari[éeo]\b", "inventarió"),
        (r"legaliz[éeo]\b", "legalizó"),
        (r"manten[íio]\b", "mantuvo"),
        (r"mejor[éeo]\b", "mejoró"),
        (r"monitore[éeo]\b", "monitoreó"),
        (r"notific[éeo]\b", "notificó"),
        (r"organiz[éeo]\b", "organizó"),
        (r"planific[éeo]\b", "planificó"),
        (r"proces[éeo]\b", "procesó"),
        (r"registr[éeo]\b", "registró"),
        (r"report[éeo]\b", "reportó"),
        (r"resolv[íio]\b", "resolvió"),
        (r"respond[íio]\b", "respondió"),
        (r"reuni[óo]\b", "reunió"),
    # Fin de verb_map

    passive_map = [
        (r"\bse realiza\b", "realizó"),
        (r"\bse realizan\b", "realizó"),
        (r"\bse realiz[óo]\b", "realizó"),
        (r"\bse efectu[óo]\b", "efectuó"),
        (r"\bse efect[uú]a\b", "efectuó"),
        (r"\bse lleva a cabo\b", "llevó a cabo"),
        (r"\bse llev[óo] a cabo\b", "llevó a cabo"),
        (r"\bse necesita\b", "requirió"),
        (r"\bse requiere\b", "requirió"),
        (r"\bse solicit[óo]\b", "solicitó"),
        (r"\bse encuentra\b", "se encontraba"),
        (r"\bse evidenci[óo]\b", "evidenció"),
        (r"\bse verifica\b", "verificó"),
        (r"\bse revisa\b", "revisó"),
        (r"\bse comunica\b", "comunicó"),
        (r"\bse inform[óo]\b", "informó"),
        (r"\bse notifica\b", "notificó"),
        (r"\bse registr[óo]\b", "registró"),
        (r"\bse reporta\b", "reportó"),
        (r"\bse consolida\b", "consolidó"),
        (r"\bse coordina\b", "coordinó"),
        (r"\bse capacita\b", "capacitó"),
        (r"\bse elabora\b", "elaboró"),
        (r"\bse entrega\b", "entregó"),
        (r"\bse presenta\b", "presentó"),
        (r"\bse eval[uú]a\b", "evaluó"),
        (r"\bse controla\b", "controló"),
    ]

def _to_third_person_text(text):
    def convert_line(line: str) -> str:
        stripped = line.strip()
        if not stripped:
            return line
        stripped = re.sub(r"^[\u2022\-\–\*\•]+\s*", "", stripped)
        lowered = stripped.lower()
        if lowered.startswith("el contratista"):
            stripped = re.sub(r"^el\s+contratista\s*[:\-–]*\s*", "", stripped, flags=re.I)
            lowered = stripped.lower()
        if lowered.startswith("yo "):
            stripped = stripped[3:].lstrip()
            lowered = stripped.lower()

        stripped = re.sub(
            r"^(Asimismo|Adicionalmente|Igualmente|En consecuencia|Por lo tanto|Por tanto|De igual manera)\b",
            lambda match: match.group(1).lower(),
            stripped,
            flags=re.I,
        )

        if re.match(r"^fuentes? de verificacion\b", stripped, re.I):
            content = stripped
            content = re.sub(r"\s*:\s*", ": ", content, count=1)
            if content and content[0].isupper():
                content = content[0].lower() + content[1:]
            return f"El contratista reportó {content}"

        for pattern, replacement in passive_map:
            stripped = re.sub(pattern, replacement, stripped, flags=re.I)
        for pattern, replacement in verb_map:
            stripped = re.sub(pattern, replacement, stripped, flags=re.I)
        if stripped.lower().startswith("durante "):
            stripped = stripped[0].lower() + stripped[1:]
        return f"El contratista {stripped}"

    # Asegurarse de que 'text' esté definido como argumento de la función
    # Ejemplo: def _to_third_person_text(text):
    return "\n".join(convert_line(line) for line in text.splitlines())

@app.route("/")
@login_required
def index():
    supervisors = list_users_by_role(ROLE_SUPERVISOR)
    return render_template(
        "index.html",
        user=_current_user(),
        supervisors=supervisors,
        output_dir=OUTPUT_DIR,
    )

@app.route("/info")
def app_info():
    routes = sorted({str(rule) for rule in app.url_map.iter_rules()})
    return jsonify({"app_name": app.name, "file": __file__, "routes": routes})

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_username(username)
        if user and check_password_hash(user.get("password_hash", ""), password):
            tab_id = _get_tab_id()
            if tab_id:
                tabs = session.get("tabs")
                if not isinstance(tabs, dict):
                    tabs = {}
                tabs[tab_id] = {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                }
                session["tabs"] = tabs
                session["boot_id"] = APP_BOOT_ID
                session.modified = True
            else:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                session["boot_id"] = APP_BOOT_ID
            next_url = request.args.get("next") or url_for("index")
            return redirect(_append_tab_id(next_url, tab_id))
        error = "Usuario o clave invalida."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    tab_id = _get_tab_id()
    if tab_id:
        tabs = session.get("tabs")
        if isinstance(tabs, dict) and tab_id in tabs:
            tabs.pop(tab_id, None)
            if tabs:
                session["tabs"] = tabs
            else:
                session.pop("tabs", None)
            session.modified = True
        return redirect(_append_tab_id(url_for("login"), tab_id))
    session.clear()
    return redirect(url_for("login"))

@app.route("/history")
@login_required
def history():
    items = list_submissions()
    return jsonify({"ok": True, "items": items})

@app.route("/history/<int:record_id>")
@login_required
def history_item(record_id: int):
    item = get_submission(record_id)
    if not item:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "item": item})

@app.route("/history/<int:record_id>/delete", methods=["POST"])
@login_required
def history_delete(record_id: int):
    if delete_submission(record_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "not_found"}), 404

@app.route("/debug/static")
@admin_required
def debug_static():
    static_dir = app.static_folder
    exists = os.path.isdir(static_dir)
    files = []
    if exists:
        try:
            files = sorted(os.listdir(static_dir))
        except OSError:
            files = []
    return jsonify({"static_folder": static_dir, "exists": exists, "files": files})

@app.route("/generate", methods=["POST"])
@login_required
def generate():
    payload = request.get_json(force=True)
    total_aportes = (
        _parse_money(payload.get("aportes_valor_salud", ""))
        + _parse_money(payload.get("aportes_valor_pension", ""))
        + _parse_money(payload.get("aportes_valor_riesgos", ""))
    )
    if total_aportes and not payload.get("total_aportes"):
        payload["total_aportes"] = _format_currency(total_aportes)
    ejecutadas_text = payload.get("obligaciones_directas_ejecutadas", "")
    payload["obligaciones_directas_ejecutadas_tercera"] = _to_third_person_text(
        ejecutadas_text
    )
    items = payload.get("obligaciones_directas_items")
    if isinstance(items, list):
        converted_items = []
        for item in items:
            if not isinstance(item, dict):
                converted_items.append(item)
                continue
            ejecutada_item = item.get("actividad_ejecutada", "")
            item_copy = dict(item)
            item_copy["actividad_ejecutada_tercera"] = _to_third_person_text(
                ejecutada_item
            )
            converted_items.append(item_copy)
        payload["obligaciones_directas_items_tercera"] = converted_items
    record_id = save_submission(payload)
    output_files = generate_documents(payload, record_id)
    files = {}
    for key, path in output_files.items():
        files[key] = {
            "name": os.path.basename(path),
            "url": url_for("download_file", record_id=record_id, doc_key=key),
        }
    return jsonify({"ok": True, "record_id": record_id, "files": files})

@app.route("/download/<int:record_id>/<doc_key>")
@login_required
def download_file(record_id: int, doc_key: str):
    filename = TEMPLATE_FILES.get(doc_key)
    if not filename:
        return jsonify({"ok": False, "error": "not_found"}), 404
    output_name = f"{record_id:05d}_{filename}"
    output_path = os.path.join(OUTPUT_DIR, output_name)
    if not os.path.isfile(output_path):
        return jsonify({"ok": False, "error": "not_found"}), 404
    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_name,
    )

def _render_admin(message: str | None = None, error: str | None = None):
    return render_template(
        "admin.html",
        roles=list_roles(),
        users=list_users(),
        doc_types=DOC_TYPES,
        message=message,
        error=error,
        user=_current_user(),
    )

@app.route("/admin")
@admin_required
def admin_panel():
    return _render_admin()

@app.route("/admin/roles", methods=["POST"])
@admin_required
def admin_create_role():
    name = request.form.get("role_name", "").strip()
    if not name:
        return _render_admin(error="El nombre del rol es obligatorio.")
    if get_role_by_name(name):
        return _render_admin(error="El rol ya existe.")
    create_role(name)
    return _render_admin(message="Rol creado correctamente.")

@app.route("/admin/roles/<int:role_id>", methods=["POST"])
@admin_required
def admin_update_role(role_id: int):
    name = request.form.get("role_name", "").strip()
    if not name:
        return _render_admin(error="El nombre del rol es obligatorio.")
    role = get_role_by_id(role_id)
    if not role:
        return _render_admin(error="Rol no encontrado.")
    if role.get("name") == ROLE_POR_ASIGNAR and name != ROLE_POR_ASIGNAR:
        return _render_admin(error="El rol por_asignar no se puede renombrar.")
    existing = get_role_by_name(name)
    if existing and existing.get("id") != role_id:
        return _render_admin(error="El rol ya existe.")
    update_role(role_id, name)
    return _render_admin(message="Rol actualizado correctamente.")

@app.route("/admin/roles/<int:role_id>/delete", methods=["POST"])
@admin_required
def admin_delete_role(role_id: int):
    role = get_role_by_id(role_id)
    if not role:
        return _render_admin(error="Rol no encontrado.")
    if role.get("name") == ROLE_POR_ASIGNAR:
        return _render_admin(error="El rol por_asignar no se puede eliminar.")
    replacement = get_role_by_name(ROLE_POR_ASIGNAR)
    if not replacement:
        replacement_id = create_role(ROLE_POR_ASIGNAR)
        replacement = {"id": replacement_id, "name": ROLE_POR_ASIGNAR}
    reassign_users_role(role_id, replacement["id"])
    delete_role(role_id)
    return _render_admin(message="Rol eliminado. Usuarios quedaron en por_asignar.")

@app.route("/admin/users", methods=["POST"])
@admin_required
def admin_create_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role_id_raw = request.form.get("role_id", "")
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    doc_type = request.form.get("doc_type", "").strip()
    doc_number = request.form.get("doc_number", "").strip()
    if not username or not password or not role_id_raw:
        return _render_admin(error="Completa usuario, clave y rol.")
    if not first_name or not last_name or not doc_type or not doc_number:
        return _render_admin(error="Completa nombres, apellidos, tipo y numero de documento.")
    if get_user_by_username(username):
        return _render_admin(error="El usuario ya existe.")
    try:
        role_id = int(role_id_raw)
    except ValueError:
        return _render_admin(error="Rol invalido.")
    role = get_role_by_id(role_id)
    if not role:
        return _render_admin(error="Rol invalido.")
    password_hash = generate_password_hash(password)
    create_user(username, password_hash, role_id, first_name, last_name, doc_type, doc_number)
    return _render_admin(message="Usuario creado correctamente.")

@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@admin_required
def admin_update_user_role(user_id: int):
    role_id_raw = request.form.get("role_id", "")
    try:
        role_id = int(role_id_raw)
    except ValueError:
        return _render_admin(error="Rol invalido.")
    role = get_role_by_id(role_id)
    if not role:
        return _render_admin(error="Rol invalido.")
    update_user_role(user_id, role_id)
    return _render_admin(message="Rol actualizado correctamente.")

@app.route("/admin/users/<int:user_id>", methods=["POST"])
@admin_required
def admin_update_user(user_id: int):
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role_id_raw = request.form.get("role_id", "")
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    doc_type = request.form.get("doc_type", "").strip()
    doc_number = request.form.get("doc_number", "").strip()
    if not username or not role_id_raw:
        return _render_admin(error="Completa usuario y rol.")
    if not first_name or not last_name or not doc_type or not doc_number:
        return _render_admin(error="Completa nombres, apellidos, tipo y numero de documento.")
    try:
        role_id = int(role_id_raw)
    except ValueError:
        return _render_admin(error="Rol invalido.")
    role = get_role_by_id(role_id)
    if not role:
        return _render_admin(error="Rol invalido.")
    existing = get_user_by_username(username)
    if existing and existing.get("id") != user_id:
        return _render_admin(error="El usuario ya existe.")
    password_hash = generate_password_hash(password) if password else None
    update_user(
        user_id,
        username,
        role_id,
        first_name,
        last_name,
        doc_type,
        doc_number,
        password_hash,
    )
    return _render_admin(message="Usuario actualizado correctamente.")

@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id: int):
    if session.get("user_id") == user_id:
        return _render_admin(error="No puedes eliminar tu propio usuario.")
    if not get_user_by_id(user_id):
        return _render_admin(error="Usuario no encontrado.")
    delete_user(user_id)
    return _render_admin(message="Usuario eliminado correctamente.")

if __name__ == "__main__":
    init_db()
    _ensure_default_roles_and_admin()
    host = "127.0.0.1"
    port = 5050
    url = f"http://{host}:{port}"
    debug = os.environ.get("FLASK_DEBUG") == "1"
    if not debug:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
