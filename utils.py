import json
import yaml
import hashlib
from pathlib import Path
from typing import Any, Tuple


def detect_and_load_spec(raw_bytes: bytes) -> Tuple[str, Any]:
    try:
        obj = json.loads(raw_bytes.decode("utf-8"))
        return "application/json", obj
    except Exception:
        pass

    try:
        obj = yaml.safe_load(raw_bytes.decode("utf-8"))
        return "application/yaml", obj
    except Exception as e:
        raise ValueError("Uploaded file is not valid JSON or YAML.") from e


def validate_openapi(obj: Any) -> None:
    if not isinstance(obj, dict):
        raise ValueError("Spec must be a JSON/YAML object.")

    openapi_version = obj.get("openapi")
    if not openapi_version:
        raise ValueError("Missing 'openapi' field at the root.")

    if not str(openapi_version).startswith("3."):
        raise ValueError(f"Only OpenAPI 3.x specs are supported (got: {openapi_version})")


def sha256_hex(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def target_folder(base_dir: Path, application: str, service: str | None) -> Path:
    safe_app = application.strip().replace("/", "_")
    safe_service = service.strip().replace("/", "_") if service else "_app_"
    folder = base_dir / safe_app / safe_service
    folder.mkdir(parents=True, exist_ok=True)
    return folder