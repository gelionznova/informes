import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(ROOT_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import app as app_module
from db import init_db, save_submission


def main() -> int:
    init_db()
    app_module._ensure_default_roles_and_admin()
    client = app_module.app.test_client()

    unauth_reports = client.get("/api/supervisor/reports")
    print("unauth_reports_status:", unauth_reports.status_code)
    assert unauth_reports.status_code == 401

    login = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    print("login_status:", login.status_code)
    assert login.status_code in (302, 303)

    payload = {
        "contratista": "Prueba Supervisor",
        "periodo_i_a": "2026-02-16",
        "obligaciones_directas_items": [
            {
                "actividad_contrato": "Actividad A",
                "actividad_ejecutada": "Ejecutada A",
                "aporta_evidencias": "NO",
            },
            {
                "actividad_contrato": "Actividad B",
                "actividad_ejecutada": "Ejecutada B",
                "aporta_evidencias": "SI",
            },
        ],
    }
    record_id = save_submission(payload)
    print("record_id:", record_id)

    reports_response = client.get("/api/supervisor/reports")
    print("auth_reports_status:", reports_response.status_code)
    assert reports_response.status_code == 200
    reports_json = reports_response.get_json() or {}
    assert reports_json.get("ok") is True

    detail_response = client.get(f"/api/supervisor/report/{record_id}")
    print("detail_status:", detail_response.status_code)
    assert detail_response.status_code == 200
    detail_json = detail_response.get_json() or {}
    assert detail_json.get("ok") is True
    assert len(detail_json.get("actividades", [])) >= 2

    review_payload = {
        "status": "pendiente",
        "observacion_global": "Revisión inicial",
        "actividades": [
            {"id": "1", "status": "cumplida", "obs": "OK"},
            {"id": "2", "status": "pendiente", "obs": "Falta soporte"},
        ],
    }
    review_response = client.post(
        f"/api/supervisor/report/{record_id}/review", json=review_payload
    )
    print("review_status:", review_response.status_code)
    assert review_response.status_code == 200
    review_json = review_response.get_json() or {}
    assert review_json.get("ok") is True

    detail_after_response = client.get(f"/api/supervisor/report/{record_id}")
    print("detail_after_status:", detail_after_response.status_code)
    assert detail_after_response.status_code == 200
    detail_after_json = detail_after_response.get_json() or {}
    assert detail_after_json.get("observacion_global") == "Revisión inicial"
    assert len(detail_after_json.get("history", [])) >= 1

    print("smoke_result: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
