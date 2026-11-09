"""Tests for AITracer saliency dispatch (local vs remote)."""

import asyncio

import numpy as np
from PIL import Image

from app.services.ai_tracer import AITracer


def test_no_saliency_tracer_is_gemini_path():
    t = AITracer(model="gemini-x")
    assert t.uses_saliency is False
    assert t._saliency_backend is None


def test_remote_tracer_builds_config_and_calls_module(monkeypatch):
    import app.services.remote_saliency as rs

    called = {}

    async def fake(cfg, image_png, target_size, **kw):
        called["cfg"] = cfg
        called["target"] = target_size
        return np.full((target_size[1], target_size[0]), 255, np.uint8)

    monkeypatch.setattr(rs, "remote_saliency_mask", fake)

    t = AITracer(saliency_tracer="fal", remote_model="fal-ai/birefnet/v2", remote_token="x")
    assert t.uses_saliency is True
    assert t._saliency_backend[0] == "fal"

    out = asyncio.run(t._saliency_on_image(Image.new("RGB", (12, 9))))
    assert out.shape == (9, 12)  # (h, w)
    assert called["cfg"].provider == "fal"
    assert called["cfg"].model == "fal-ai/birefnet/v2"
    assert called["target"] == (12, 9)  # (w, h)


def test_ai_tracer_unload(monkeypatch):
    t = AITracer(saliency_tracer="fal", remote_model="fal-ai/birefnet/v2", remote_token="x")
    assert t._saliency_backend is not None
    t.unload()
    assert t._saliency_backend is None


def test_get_tracer_evicts_other_local_tracers(monkeypatch):
    from app.api import routes

    routes._tracers.clear()
    monkeypatch.setattr(routes.settings, "tracers", "inspyrenet,birefnet-lite")

    fake_unloaded = []

    class FakeLocalTracer:
        def __init__(self, name):
            self.name = name
        def unload(self):
            fake_unloaded.append(self.name)

    monkeypatch.setattr(routes, "AITracer", lambda saliency_tracer=None, **k: FakeLocalTracer(saliency_tracer))

    t1 = routes._get_tracer("inspyrenet")
    assert "inspyrenet" in routes._tracers
    assert fake_unloaded == []

    # Requesting a different local tracer should evict the previous one
    t2 = routes._get_tracer("birefnet-lite")
    assert "birefnet-lite" in routes._tracers
    assert "inspyrenet" not in routes._tracers
    assert fake_unloaded == ["inspyrenet"]

    routes._tracers.clear()

