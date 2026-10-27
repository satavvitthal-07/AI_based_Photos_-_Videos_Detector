from pathlib import Path

from backend.app import create_app


def test_health_reports_backend_and_detector_status(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["detector"]["configured"] is False
    assert body["detector"]["available"] is False


def test_root_serves_frontend_landing_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"TruthLens AI" in response.data


def test_frontend_assets_and_api_remain_available(client):
    css_response = client.get("/css/base.css")
    js_response = client.get("/js/app.js")
    api_response = client.get("/api/health")

    assert css_response.status_code == 200
    assert css_response.mimetype == "text/css"
    assert js_response.status_code == 200
    assert js_response.mimetype == "text/javascript"
    assert api_response.status_code == 200


def test_backend_origin_can_load_frontend_module_scripts(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": Path(tmp_path) / "same-origin.sqlite3",
        }
    )

    response = app.test_client().get(
        "/js/upload.js",
        headers={"Origin": "http://127.0.0.1:5000"},
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5000"
