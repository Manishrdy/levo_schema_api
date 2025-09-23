from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path

from database import SessionLocal
from models import Base, Application, Service, SchemaVersion
from utils import detect_and_load_spec, validate_openapi, sha256_hex, target_folder

from fastapi.responses import FileResponse
from fastapi import Query

from database import engine
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Levo Schema API", version="0.1.0")

DATA_DIR = Path("data")

def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


@app.get("/healthz")
def health():
    print("Health check endpoint called")
    return {"status": "ok"}

@app.post("/schemas/upload")
async def upload_schema(
    application: str = Form(...),
    service: str = Form(None),
    spec: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    print(f"Upload schema called with application: {application}, service: {service}")
    raw = await spec.read()

    try:
        media_type, parsed_obj = detect_and_load_spec(raw)
        validate_openapi(parsed_obj)
    except Exception as e:
        print(f"Invalid OpenAPI spec: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid OpenAPI spec: {e}")

    checksum = sha256_hex(raw)

    app_obj = db.query(Application).filter_by(name=application).first()
    if not app_obj:
        app_obj = Application(name=application)
        db.add(app_obj)
        db.flush()

    svc = None
    if service:
        svc = db.query(Service).filter_by(application_id=app_obj.id, name=service).first()
        if not svc:
            svc = Service(application_id=app_obj.id, name=service)
            db.add(svc)
            db.flush()

    existing_versions = (
        db.query(SchemaVersion)
        .filter_by(application_id=app_obj.id, service_id=svc.id if svc else None)
        .count()
    )
    version = existing_versions + 1

    ext = ".json" if media_type == "application/json" else ".yaml"
    folder = target_folder(DATA_DIR, application, service)
    file_path = folder / f"v{version}{ext}"
    file_path.write_bytes(raw)

    record = SchemaVersion(
        application_id=app_obj.id,
        service_id=svc.id if svc else None,
        version=version,
        path=str(file_path),
        media_type=media_type,
        checksum=checksum,
        uploaded_at=datetime.utcnow(),
    )
    db.add(record)
    db.flush()

    result = {
        "application": application,
        "service": service,
        "version": version,
        "media_type": media_type,
        "checksum": checksum,
        "path": str(file_path),
        "uploaded_at": record.uploaded_at.isoformat(),
    }
    print(f"Schema uploaded successfully: {result}")
    return result

@app.get("/schemas")
def get_schema(
    application: str = Query(...),
    service: str = Query(default=None),
    version: int = Query(default=None),
    db: Session = Depends(get_db)
):
    print(f"Get schema called with application: {application}, service: {service}, version: {version}")
    app_obj = db.query(Application).filter_by(name=application).first()
    if not app_obj:
        print("Application not found")
        raise HTTPException(status_code=404, detail="Application not found")

    svc = None
    if service:
        svc = db.query(Service).filter_by(application_id=app_obj.id, name=service).first()
        if not svc:
            print("Service not found")
            raise HTTPException(status_code=404, detail="Service not found")

    query = db.query(SchemaVersion).filter_by(
        application_id=app_obj.id,
        service_id=svc.id if svc else None
    )

    if version:
        query = query.filter_by(version=version)
    else:
        query = query.order_by(SchemaVersion.version.desc()).limit(1)

    schema = query.first()
    if not schema:
        print("Schema not found")
        raise HTTPException(status_code=404, detail="Schema not found")

    print(f"Schema retrieved successfully: {schema.path}")
    return FileResponse(
        path=schema.path,
        media_type=schema.media_type,
        filename=schema.path.split("/")[-1]
    )

@app.get("/schemas/versions")
def list_versions(
    application: str = Query(...),
    service: str = Query(default=None),
    db: Session = Depends(get_db)
):
    print(f"List versions called with application: {application}, service: {service}")
    app_obj = db.query(Application).filter_by(name=application).first()
    if not app_obj:
        print("Application not found")
        raise HTTPException(status_code=404, detail="Application not found")

    svc = None
    if service:
        svc = db.query(Service).filter_by(application_id=app_obj.id, name=service).first()
        if not svc:
            print("Service not found")
            raise HTTPException(status_code=404, detail="Service not found")

    versions = db.query(SchemaVersion).filter_by(
        application_id=app_obj.id,
        service_id=svc.id if svc else None
    ).order_by(SchemaVersion.version.asc()).all()

    result = {
        "application": application,
        "service": service,
        "versions": [
            {
                "version": v.version,
                "uploaded_at": v.uploaded_at.isoformat(),
                "media_type": v.media_type,
                "checksum": v.checksum,
                "path": v.path
            }
            for v in versions
        ]
    }
    print(f"Versions listed successfully: {result}")
    return result