# test_utils_local.py
from pathlib import Path
from utils import detect_and_load_spec, validate_openapi, sha256_hex

spec_path = Path("data/sample.yaml")  # <- change to your test file
raw = spec_path.read_bytes()

# Parse
media_type, parsed = detect_and_load_spec(raw)
print(f"Parsed as: {media_type}")

# Validate
try:
    validate_openapi(parsed)
    print("✅ OpenAPI spec is valid!")
except Exception as e:
    print(f"❌ Validation failed: {e}")

# Checksum
digest = sha256_hex(raw)
print(f"SHA256: {digest}")