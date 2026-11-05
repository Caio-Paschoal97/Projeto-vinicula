"""RBAC: as rotas analíticas exigem as permissões do catálogo da API Java.

O Java é a autoridade (JWT + role_permissions); o Python consome as permissões
efetivas devolvidas em /api/auth/me e bloqueia com 403 quem não as possui.
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
import httpx
from rbac_catalog import permissions_for

from app.config import Settings
from app.main import create_app

KEY = "k" * 40
AUTH = {"Authorization": "Bearer user-jwt"}


def _fake_java(role: str = "PRODUCER", permissions: list[str] | None = None):
    keys = permissions_for(role) if permissions is None else permissions

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/auth/me":
            return httpx.Response(200, json={
                "id": "11111111-1111-4111-8111-111111111111", "name": "U", "email": "u@a.test",
                "roleKey": role, "role": role, "status": "ACTIVE", "permissionKeys": keys})
        if path == "/api/plantations":
            return httpx.Response(200, json=[])
        if path == "/api/internal/climate-readings":
            captured = (datetime.now(UTC) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            return httpx.Response(200, json=[{
                "channelId": "1", "entryId": 1, "capturedAt": captured,
                "measurements": {"temperature": 28.0, "humidity": 60.0}, "qualityStatus": "VALID"}])
        return httpx.Response(404, json={"message": "?"})

    return handler


def _get(fake, path: str) -> httpx.Response:
    app = create_app(Settings(java_api_url="http://java.test", internal_api_key=KEY))
    with TestClient(app) as client:
        app.state.http_client = httpx.AsyncClient(transport=httpx.MockTransport(fake))
        return client.get(path, headers=AUTH)


def test_producer_with_monitoring_permission_reads_climate():
    response = _get(_fake_java("PRODUCER"), "/api/v1/climate/current")
    assert response.status_code == 200


def test_producer_without_monitoring_permission_is_forbidden():
    keys = [key for key in permissions_for("PRODUCER") if key != "monitoring.view"]
    response = _get(_fake_java("PRODUCER", keys), "/api/v1/climate/current")
    assert response.status_code == 403
    assert "permissão" in response.json()["message"]


def test_profile_without_permissions_is_denied_by_default():
    response = _get(_fake_java("PRODUCER", []), "/api/v1/dashboard/summary")
    assert response.status_code == 403


def test_legacy_profile_without_permission_keys_is_denied():
    async def legacy(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/me":
            return httpx.Response(200, json={
                "id": "11111111-1111-4111-8111-111111111111", "name": "U", "email": "u@a.test",
                "roleKey": "PRODUCER", "role": "PRODUCER", "status": "ACTIVE"})
        return httpx.Response(404, json={"message": "?"})

    response = _get(legacy, "/api/v1/dashboard/summary")
    assert response.status_code == 403


def test_producer_without_analytics_permission_cannot_open_forecast_or_market():
    keys = [key for key in permissions_for("PRODUCER") if key != "analytics.view"]
    fake = _fake_java("PRODUCER", keys)
    assert _get(fake, "/api/v1/dashboard/forecast").status_code == 403
    assert _get(fake, "/api/v1/dashboard/market").status_code == 403


def test_admin_keeps_access_to_analytics_and_climate():
    fake = _fake_java("ADMIN")
    assert _get(fake, "/api/v1/climate/current").status_code == 200
    assert _get(fake, "/api/v1/dashboard/analyst").status_code == 200


def test_analyst_role_still_required_for_analyst_dashboard():
    # PRODUCER com analytics.view não abre o painel analítico (regra de papel preservada).
    fake = _fake_java("PRODUCER")
    assert _get(fake, "/api/v1/dashboard/analyst").status_code == 403
