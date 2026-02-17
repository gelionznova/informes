# --- ENDPOINTS SUPERVISOR ---
from datetime import datetime




import os
import re
import sys
import threading
import unicodedata
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
    update_submission_data,
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

ALLOWED_REVIEW_STATUS = {"pendiente", "aprobado", "rechazado"}
ALLOWED_ACTIVITY_STATUS = {"cumplida", "no cumplida", "pendiente"}

verb_map = [
    (r"aprob[éeo]\b", "aprobó"),
    (r"apoy[éeo]\b", "apoyó"),
    (r"archiv[éeo]\b", "archivó"),
    (r"asist[íio]\b", "asistió"),
    (r"asesor[éeo]\b", "asesoró"),
    (r"atend[íio]\b", "atendió"),
    (r"busc[éeo]\b", "buscó"),
    (r"capacit[éeo]\b", "capacitó"),
    (r"certific[éeo]\b", "certificó"),
    (r"comunic[éeo]\b", "comunicó"),
    (r"consolid[éeo]\b", "consolidó"),
    (r"coordin[éeo]\b", "coordinó"),
    (r"control[éeo]\b", "controló"),
    (r"correspond[íio]\b", "correspondió"),
    (r"cumpl[íio]\b", "cumplió"),
    (r"custodi[éeo]\b", "custodió"),
    (r"digitaliz[éeo]\b", "digitalizó"),
    (r"diligenci[éeo]\b", "diligenció"),
    (r"elabor[éeo]\b", "elaboró"),
    (r"elimin[éeo]\b", "eliminó"),
    (r"emit[íio]\b", "emitió"),
    (r"envi[éeo]\b", "envió"),
    (r"evalu[éeo]\b", "evaluó"),
    (r"exped[íio]\b", "expidió"),
    (r"facilit[éeo]\b", "facilitó"),
    (r"formaliz[éeo]\b", "formalizó"),
    (r"gestion[éeo]\b", "gestionó"),
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
    (r"realic[éeo]\b", "realizó"),
    (r"realiz[éeo]\b", "realizó"),
    (r"redact[éeo]\b", "redactó"),
    (r"registr[éeo]\b", "registró"),
    (r"report[éeo]\b", "reportó"),
    (r"revis[éeo]\b", "revisó"),
    (r"resolv[íio]\b", "resolvió"),
    (r"respond[íio]\b", "respondió"),
    (r"reuni[óo]\b", "reunió"),
    (r"socializ[éeo]\b", "socializó"),
    (r"tramit[éeo]\b", "tramitó"),
    (r"verific[éeo]\b", "verificó"),
]

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

def _parse_money(value) -> float:
    if value is None:
        return 0.0
    raw = str(value).strip()
    if not raw:
        return 0.0
    cleaned = re.sub(r"[^0-9,.-]+", "", raw)
    if not cleaned:
        return 0.0
    if "," in cleaned:
        normalized = cleaned.replace(".", "").replace(",", ".")
    else:
        normalized = cleaned.replace(".", "")
    try:
        return float(normalized)
    except ValueError:
        return 0.0

def _format_currency(value: float) -> str:
    amount = int(round(float(value)))
    return f"$ {amount:,}".replace(",", ".")

def _extract_period_key(data: dict) -> str:
    raw_value = (
        data.get("periodo_i_a")
        or data.get("periodo_i_de")
        or data.get("fecha_presentacion_informe")
        or ""
    )
    raw_value = str(raw_value).strip()
    if not raw_value:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw_value):
        return raw_value[:7]
    match = re.match(r"^\d{1,2}/(\d{1,2})/(\d{2}|\d{4})$", raw_value)
    if not match:
        return ""
    month = int(match.group(1))
    year = match.group(2)
    year = f"20{year}" if len(year) == 2 else year
    return f"{year}-{month:02d}"

def _build_default_review_activities(data: dict) -> list[dict]:
    items = data.get("obligaciones_directas_items")
    if not isinstance(items, list):
        return []
    result = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            contract_activity = str(item.get("actividad_contrato", "")).strip()
            executed_activity = str(item.get("actividad_ejecutada", "")).strip()
            evidence_payload = item.get("evidencias") if isinstance(item.get("evidencias"), dict) else {}
            evidence_images = evidence_payload.get("images") if isinstance(evidence_payload.get("images"), list) else []
            evidence_groups = evidence_payload.get("groups") if isinstance(evidence_payload.get("groups"), list) else []

            normalized_groups = []
            total_groups = max(1, (len(evidence_images) + 2) // 3) if evidence_images else 0
            for group_index in range(total_groups):
                group_info = (
                    evidence_groups[group_index]
                    if group_index < len(evidence_groups)
                    and isinstance(evidence_groups[group_index], dict)
                    else {}
                )
                chunk = evidence_images[group_index * 3 : (group_index + 1) * 3]
                photos = []
                for image in chunk:
                    if not isinstance(image, dict):
                        continue
                    data_url = str(image.get("dataUrl", "")).strip()
                    if not data_url:
                        continue
                    photos.append(
                        {
                            "name": str(image.get("name", "Foto")).strip() or "Foto",
                            "url": data_url,
                        }
                    )
                if photos or group_info.get("description") or group_info.get("date"):
                    normalized_groups.append(
                        {
                            "description": str(group_info.get("description", "")).strip(),
                            "date": str(group_info.get("date", "")).strip(),
                            "photos": photos,
                        }
                    )
        else:
            contract_activity = str(item).strip()
            executed_activity = ""
            normalized_groups = []

        desc = contract_activity or executed_activity
        result.append(
            {
                "id": str(index),
                "desc": desc,
                "contract_activity": contract_activity,
                "executed_activity": executed_activity,
                "evidence_groups": normalized_groups,
                "status": "pendiente",
                "obs": "",
            }
        )
    return result

def _merge_review_activities(defaults: list[dict], saved: list[dict]) -> list[dict]:
    saved_by_id = {}
    for item in saved:
        if not isinstance(item, dict):
            continue
        act_id = str(item.get("id", "")).strip()
        if not act_id:
            continue
        saved_by_id[act_id] = {
            "id": act_id,
            "desc": str(item.get("desc", "")).strip(),
            "status": str(item.get("status", "pendiente")).strip().lower(),
            "obs": str(item.get("obs", "")).strip(),
        }

    merged = []
    seen = set()
    for default in defaults:
        act_id = str(default.get("id", "")).strip()
        if not act_id:
            continue
        seen.add(act_id)
        saved_item = saved_by_id.get(act_id, {})
        status = saved_item.get("status", default.get("status", "pendiente"))
        if status not in ALLOWED_ACTIVITY_STATUS:
            status = "pendiente"
        merged.append(
            {
                "id": act_id,
                "desc": saved_item.get("desc") or str(default.get("desc", "")).strip(),
                "contract_activity": str(default.get("contract_activity", "")).strip(),
                "executed_activity": str(default.get("executed_activity", "")).strip(),
                "evidence_groups": default.get("evidence_groups", []) if isinstance(default.get("evidence_groups"), list) else [],
                "status": status,
                "obs": saved_item.get("obs", ""),
            }
        )

    for act_id, item in saved_by_id.items():
        if act_id in seen:
            continue
        status = item.get("status", "pendiente")
        if status not in ALLOWED_ACTIVITY_STATUS:
            status = "pendiente"
        merged.append(
            {
                "id": act_id,
                "desc": item.get("desc", ""),
                "contract_activity": "",
                "executed_activity": "",
                "evidence_groups": [],
                "status": status,
                "obs": item.get("obs", ""),
            }
        )
    return merged

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

def supervisor_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = _current_user()
        if not user:
            return jsonify({"ok": False, "error": "auth_required"}), 401
        if user.get("role") not in {ROLE_SUPERVISOR, ROLE_SUPER_ADMIN}:
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


_FIRST_PERSON_TO_THIRD_IRREGULAR = {
    "fui": "fue",
    "di": "dio",
    "vi": "vio",
    "hice": "hizo",
    "traje": "trajo",
    "dije": "dijo",
    "puse": "puso",
    "estuve": "estuvo",
    "tuve": "tuvo",
}


def _convert_first_person_verb(word: str) -> str:
    low = unicodedata.normalize("NFC", word.lower())
    if low in _FIRST_PERSON_TO_THIRD_IRREGULAR:
        converted = _FIRST_PERSON_TO_THIRD_IRREGULAR[low]
    elif low.endswith("gué") and len(low) > 3:
        converted = low[:-3] + "gó"
    elif low.endswith("qué") and len(low) > 3:
        converted = low[:-3] + "có"
    elif low.endswith("cé") and len(low) > 2:
        converted = low[:-2] + "zó"
    elif low.endswith("é") and len(low) > 2:
        converted = low[:-1] + "ó"
    elif low.endswith("í") and len(low) > 1:
        converted = low[:-1] + "ió"
    else:
        return word

    if word.isupper():
        return converted.upper()
    if word and word[0].isupper():
        return converted.capitalize()
    return converted


def _convert_first_person_fallback(text: str) -> str:
    words = re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", text, flags=re.UNICODE)
    if not words:
        return text

    for word in words:
        converted = _convert_first_person_verb(word)
        if converted != word:
            return re.sub(
                rf"\b{re.escape(word)}\b",
                converted,
                text,
                count=1,
                flags=re.IGNORECASE,
            )
    return text


def _normalize_first_person_pronouns(text: str) -> str:
    replacements = [
        (r"\bconmigo\b", "con él"),
        (r"\bpara mí\b", "para él"),
        (r"\bmi\s+(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", "su "),
        (r"\bmis\s+(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", "sus "),
        (r"\bme\b", "se"),
    ]
    normalized = text
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.I)
    return normalized

def _to_third_person_text(text):
    def convert_line(line: str) -> str:
        stripped = line.strip()
        if not stripped:
            return line
        stripped = unicodedata.normalize("NFC", stripped)
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

        if re.match(r"^fuentes?\s+de\s+verificaci[oó]n\b", stripped, re.I):
            content = stripped
            content = re.sub(r"\s*:\s*", ": ", content, count=1)
            if content and content[0].isupper():
                content = content[0].lower() + content[1:]
            return f"El contratista reportó {content}"

        for pattern, replacement in passive_map:
            stripped = re.sub(pattern, replacement, stripped, flags=re.I)

        before_verbs = stripped
        for pattern, replacement in verb_map:
            stripped = re.sub(pattern, replacement, stripped, flags=re.I)

        if stripped == before_verbs:
            stripped = _convert_first_person_fallback(stripped)

        stripped = _normalize_first_person_pronouns(stripped)

        if stripped.lower().startswith("durante "):
            stripped = stripped[0].lower() + stripped[1:]
        return f"El contratista {stripped}"

    return "\n".join(convert_line(line) for line in text.splitlines())

def _build_review_action(status: str) -> str:
    if status == "aprobado":
        return "Informe aprobado"
    if status == "rechazado":
        return "Informe rechazado"
    return "Revisión parcial guardada"

def _build_supervisor_reports() -> list[dict]:
    reports = []
    for item in list_submissions(limit=200):
        data = item.get("data") or {}
        review = data.get("supervisor_review") if isinstance(data.get("supervisor_review"), dict) else {}
        status = str(review.get("status", "pendiente")).lower()
        if status not in ALLOWED_REVIEW_STATUS:
            status = "pendiente"
        reports.append(
            {
                "id": item["id"],
                "contractor": str(data.get("contratista", "")).strip(),
                "period": _extract_period_key(data),
                "status": status,
                "docUrl": url_for("download_file", record_id=item["id"], doc_key="inf_supervision"),
            }
        )
    return reports

def _build_supervisor_detail(record_id: int) -> tuple[dict | None, int]:
    item = get_submission(record_id)
    if not item:
        return {"ok": False, "error": "not_found"}, 404
    data = item.get("data") or {}
    review = data.get("supervisor_review") if isinstance(data.get("supervisor_review"), dict) else {}
    default_activities = _build_default_review_activities(data)
    saved_activities = review.get("actividades") if isinstance(review.get("actividades"), list) else []
    activities = _merge_review_activities(default_activities, saved_activities)
    history = review.get("history") if isinstance(review.get("history"), list) else []
    summary = {
        "informe_no": str(data.get("informe_no", "")).strip(),
        "contratista": str(data.get("contratista", "")).strip(),
        "contrato_no": str(data.get("contrato_no", "")).strip(),
        "objeto_contractual": str(data.get("objeto_contractual", "")).strip(),
        "periodo": _extract_period_key(data),
    }
    return (
        {
            "ok": True,
            "id": record_id,
            "status": review.get("status", "pendiente"),
            "observacion_global": review.get("observacion_global", ""),
            "summary": summary,
            "actividades": activities,
            "history": history,
        },
        200,
    )

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

@app.route("/api/supervisor/reports")
@supervisor_required
def supervisor_reports():
    return jsonify({"ok": True, "reports": _build_supervisor_reports()})

@app.route("/api/supervisor/report/<int:record_id>")
@supervisor_required
def supervisor_report_detail(record_id: int):
    payload, status_code = _build_supervisor_detail(record_id)
    return jsonify(payload), status_code

@app.route("/api/supervisor/report/<int:record_id>/review", methods=["POST"])
@supervisor_required
def supervisor_report_review(record_id: int):
    item = get_submission(record_id)
    if not item:
        return jsonify({"ok": False, "error": "not_found"}), 404

    current_data = item.get("data") or {}
    current_review = current_data.get("supervisor_review") if isinstance(current_data.get("supervisor_review"), dict) else {}
    current_history = current_review.get("history") if isinstance(current_review.get("history"), list) else []

    payload = request.get_json(force=True) or {}
    status = str(payload.get("status", "pendiente")).strip().lower()
    if status not in ALLOWED_REVIEW_STATUS:
        status = "pendiente"

    incoming_activities = payload.get("actividades")
    normalized_activities = []
    if isinstance(incoming_activities, list):
        for activity in incoming_activities:
            if not isinstance(activity, dict):
                continue
            act_id = str(activity.get("id", "")).strip()
            if not act_id:
                continue
            act_status = str(activity.get("status", "pendiente")).strip().lower()
            if act_status not in ALLOWED_ACTIVITY_STATUS:
                act_status = "pendiente"
            normalized_activities.append(
                {
                    "id": act_id,
                    "desc": str(activity.get("desc", "")).strip(),
                    "status": act_status,
                    "obs": str(activity.get("obs", "")).strip(),
                }
            )

    if status == "aprobado":
        if normalized_activities:
            activities_to_validate = normalized_activities
        else:
            default_activities = _build_default_review_activities(current_data)
            saved_activities = current_review.get("actividades") if isinstance(current_review.get("actividades"), list) else []
            activities_to_validate = _merge_review_activities(default_activities, saved_activities)

        if any(
            str(activity.get("status", "")).strip().lower() != "cumplida"
            for activity in activities_to_validate
            if isinstance(activity, dict)
        ):
            return jsonify({"ok": False, "error": "activities_not_completed"}), 400

    user = _current_user() or {}
    history_entry = {
        "date": datetime.utcnow().replace(microsecond=0).isoformat(),
        "action": _build_review_action(status),
        "status": status,
        "by": user.get("username", "supervisor"),
    }
    current_history.append(history_entry)

    current_data["supervisor_review"] = {
        "status": status,
        "observacion_global": str(payload.get("observacion_global", "")).strip(),
        "actividades": normalized_activities,
        "history": current_history,
    }

    if not update_submission_data(record_id, current_data):
        return jsonify({"ok": False, "error": "not_found"}), 404

    return jsonify({"ok": True})

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
