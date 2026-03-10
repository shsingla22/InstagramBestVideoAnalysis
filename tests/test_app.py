"""Tests for the FastAPI application endpoints."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.app import app


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "app" in data
    assert data["app"] == "ok"
    assert "vllm" in data


def test_dashboard_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Instagram Reel Analyzer" in resp.text


def test_creators_endpoint(client):
    resp = client.get("/api/creators")
    assert resp.status_code == 200
    creators = resp.json()
    assert len(creators) >= 10


def test_results_endpoint(client):
    resp = client.get("/api/results")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_stats_endpoint(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_analyzed" in stats
    assert "avg_virality" in stats


def test_upload_no_file(client):
    resp = client.post("/api/analyze")
    assert resp.status_code == 422  # validation error


def test_upload_bad_extension(client):
    resp = client.post(
        "/api/analyze",
        files={"file": ("test.txt", b"not a video", "text/plain")},
    )
    assert resp.status_code == 400


def test_result_not_found(client):
    resp = client.get("/api/results/nonexistent")
    assert resp.status_code == 404
