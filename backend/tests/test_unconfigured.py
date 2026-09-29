"""When Hindsight is not configured, the app must fail loudly - never fake memory."""
from app.core.config import Settings
from app.services import hindsight_service as hs


def test_settings_not_configured():
    s = Settings(hindsight_api_key=None, hindsight_base_url=None, _env_file=None)
    assert s.hindsight_configured is False and s.hindsight_mode == "not-configured"


def test_settings_cloud_and_self_hosted():
    assert Settings(hindsight_api_key="k", hindsight_base_url=None, _env_file=None).hindsight_mode == "cloud"
    assert Settings(hindsight_base_url="http://localhost:8888", _env_file=None).hindsight_mode == "self-hosted"


def test_503_when_unconfigured(client, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.get_settings(), "hindsight_api_key", None)
    monkeypatch.setattr(config.get_settings(), "hindsight_base_url", None)
    hs.reset_client()
    cid = client.post("/api/customers", json={"name": "N", "company": "C"}).json()["id"]
    i = client.post(f"/api/customers/{cid}/interactions", json={"content": "x"})
    assert i.status_code == 201 and i.json()["retained"] is False
    assert "not configured" in i.json()["retain_error"].lower()
    r = client.post(f"/api/customers/{cid}/ask", json={"question": "hi"})
    assert r.status_code == 503 and r.json()["code"] == "hindsight_not_configured"
    st = client.get("/api/memory/status").json()
    assert st["configured"] is False and st["reachable"] is False


def test_placeholder_values_count_as_unset():
    s = Settings(hindsight_api_key="your_key_here", hindsight_base_url="", _env_file=None)
    assert s.hindsight_configured is False
