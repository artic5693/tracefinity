"""Route-level tests for remote tracers."""

from fastapi.testclient import TestClient

import app.api.routes as routes
from app.config import ensure_user_dirs
from app.main import app
from app.models.schemas import Session


def _client(tmp_path, monkeypatch):
    monkeypatch.setattr(routes.settings, "storage_path", tmp_path)
    routes._store_cache.clear()
    routes._tracers.clear()
    ensure_user_dirs(tmp_path / "default")
    return TestClient(app)


def test_api_keys_reports_remote_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(routes.settings, "tracers", "fal")
    monkeypatch.setattr(routes.settings, "fal_key", "fal_x")
    client = _client(tmp_path, monkeypatch)

    body = client.get("/api/api-keys").json()
    assert body["google"] is True
    assert body["provider"] == "remote"
    assert {"id": "fal", "label": "fal.ai"} in body["tracers"]


def test_trace_remote_missing_token_returns_400(tmp_path, monkeypatch):
    monkeypatch.setattr(routes.settings, "tracers", "fal")
    monkeypatch.setattr(routes.settings, "fal_key", None)
    client = _client(tmp_path, monkeypatch)

    sessions, _, _ = routes.get_stores("default")
    sessions.set("s1", Session(id="s1", corrected_image_path="default/processed/x.png"))

    resp = client.post("/api/sessions/s1/trace", json={"tracer": "fal"})
    assert resp.status_code == 400
    assert "token" in resp.json()["detail"].lower()


def _seed_remote_session(tmp_path, monkeypatch):
    monkeypatch.setattr(routes.settings, "tracers", "fal")
    monkeypatch.setattr(routes.settings, "fal_key", "fal_x")
    client = _client(tmp_path, monkeypatch)
    proc = tmp_path / "default" / "processed"
    proc.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    Image.new("RGB", (32, 32), "white").save(proc / "c.png")
    sessions, _, _ = routes.get_stores("default")
    sessions.set("s1", Session(id="s1", corrected_image_path="default/processed/c.png"))
    return client


def test_trace_remote_provider_error_returns_502(tmp_path, monkeypatch):
    import httpx

    import app.services.remote_saliency as rs
    client = _seed_remote_session(tmp_path, monkeypatch)

    async def boom(*a, **k):
        raise httpx.HTTPStatusError(
            "500", request=httpx.Request("POST", "https://fal.run/x"), response=httpx.Response(500)
        )

    monkeypatch.setattr(rs, "remote_saliency_mask", boom)
    resp = client.post("/api/sessions/s1/trace", json={"tracer": "fal"})
    assert resp.status_code == 502
    assert "fal.ai" in resp.json()["detail"]


def test_trace_remote_timeout_message_is_provider_aware(tmp_path, monkeypatch):
    import app.services.remote_saliency as rs
    client = _seed_remote_session(tmp_path, monkeypatch)

    async def slow(*a, **k):
        raise TimeoutError()

    monkeypatch.setattr(rs, "remote_saliency_mask", slow)
    resp = client.post("/api/sessions/s1/trace", json={"tracer": "fal"})
    assert resp.status_code == 504
    assert "Gemini" not in resp.json()["detail"]
    assert "fal.ai" in resp.json()["detail"]


def test_trace_from_mask_aligns_only_when_dimensions_differ(tmp_path, monkeypatch):
    import io
    from PIL import Image

    monkeypatch.setattr(routes.settings, "tracers", "isnet")
    client = _client(tmp_path, monkeypatch)
    proc = tmp_path / "default" / "processed"
    proc.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (200, 100), "white").save(proc / "c.png")
    sessions, _, _ = routes.get_stores("default")
    sessions.set("s1", Session(id="s1", corrected_image_path="default/processed/c.png"))

    align_calls: list[bool] = []

    class FakeTracer:
        def _trace_mask(self, mask_path, original_path, align=False):
            align_calls.append(align)
            return [([(10.0, 10.0), (50.0, 10.0), (50.0, 50.0), (10.0, 50.0)], [])]

    monkeypatch.setattr(routes, "_get_tracer", lambda *a, **k: FakeTracer())

    same_buf = io.BytesIO()
    Image.new("RGB", (200, 100), "white").save(same_buf, format="PNG")
    resp_same = client.post(
        "/api/sessions/s1/trace-mask",
        files={"mask": ("mask.png", same_buf.getvalue(), "image/png")},
    )
    assert resp_same.status_code == 200
    assert align_calls == [False]

    diff_buf = io.BytesIO()
    Image.new("RGB", (160, 80), "white").save(diff_buf, format="PNG")
    resp_diff = client.post(
        "/api/sessions/s1/trace-mask",
        files={"mask": ("mask.png", diff_buf.getvalue(), "image/png")},
    )
    assert resp_diff.status_code == 200
    assert align_calls == [False, True]

