import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import pytest
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from main import app
from models import Base
from database import engine

client = TestClient(app)

DATA_DIR = Path("data")

VALID_YAML = b"""
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /hello:
    get:
      summary: Say hello
      responses:
        '200':
          description: OK
"""

INVALID_YAML = b"not a real openapi spec"

@pytest.fixture(autouse=True)
def clean_env():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Clean data folder
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    yield

def test_upload_app_level_schema():
    response = client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "app-only"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert body["application"] == "app-only"
    assert body["service"] is None


def test_upload_service_level_schema():
    response = client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "app1", "service": "svc1"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert body["service"] == "svc1"


def test_version_increments_on_upload():
    r1 = client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "app1", "service": "svc2"}
    )
    assert r1.status_code == 200
    assert r1.json()["version"] == 1

    # v2
    r2 = client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "app1", "service": "svc2"}
    )
    assert r2.status_code == 200
    assert r2.json()["version"] == 2


def test_get_latest_schema():
    client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "app-latest", "service": "svc-latest"}
    )

    res = client.get("/schemas", params={"application": "app-latest", "service": "svc-latest"})
    assert res.status_code == 200
    assert b"openapi:" in res.content


def test_get_specific_version():
    client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "appX", "service": "svcX"}
    )
    client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "appX", "service": "svcX"}
    )

    res = client.get("/schemas", params={"application": "appX", "service": "svcX", "version": 1})
    assert res.status_code == 200
    assert b"openapi:" in res.content


def test_list_versions():
    client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "myapp", "service": "svcY"}
    )
    client.post(
        "/schemas/upload",
        files={"spec": ("openapi.yaml", VALID_YAML)},
        data={"application": "myapp", "service": "svcY"}
    )

    res = client.get("/schemas/versions", params={"application": "myapp", "service": "svcY"})
    assert res.status_code == 200
    body = res.json()
    assert body["application"] == "myapp"
    assert len(body["versions"]) == 2
    assert body["versions"][0]["version"] == 1
    assert body["versions"][1]["version"] == 2


def test_invalid_openapi_is_rejected():
    res = client.post(
        "/schemas/upload",
        files={"spec": ("bad.yaml", INVALID_YAML)},
        data={"application": "badapp"}
    )
    assert res.status_code == 400
    assert "Invalid OpenAPI" in res.text


def test_upload_without_spec_fails():
    res = client.post(
        "/schemas/upload",
        data={"application": "no-file"}
    )
    assert res.status_code == 422