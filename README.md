# Levo Schema API – Take Home Assignment ✅

A minimal FastAPI-based REST API for uploading, validating, versioning, and retrieving OpenAPI spec files (`.json` or `.yaml`) at the application and optional service level — inspired by Levo CLI (`levo import`, `levo test`).

---

## 🚀 Features

- ✅ Upload OpenAPI 3.x specs (YAML or JSON)
- ✅ Validate file format and version
- ✅ Version schema uploads per app/service
- ✅ Store original files in `./data/`
- ✅ Track uploads in `levo.db` (SQLite)
- ✅ Retrieve latest or specific versions
- ✅ List all uploaded versions
- ✅ View data via web GUI (`sqlite-web`)
- ✅ Run unit tests with `pytest`

---

## ⚙️ Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd levo_schema_api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Running the API Server

```
uvicorn main:app --reload
```

### 3. Curls collection to test from postman

```
https://grey-moon-445797.postman.co/workspace/Manish~283d32b7-e13d-4cd5-a9d8-96c6fb685e4b/collection/17079845-008e2c60-882e-4508-aa38-c8d4bf3cff9e?action=share&creator=17079845
```

### 4. Run all testcases
```
pytest -q tests/
```

### 5. View database
Install the dependency
```
pip install sqlite-web
```

Run the GUI
```
python -m sqlite_web levo.db
```

