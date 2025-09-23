from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Application(Base):
    __tablename__ = "applications"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(255), unique=True, index=True)

    services = relationship("Service", back_populates="application", cascade="all, delete-orphan")
    versions = relationship("SchemaVersion", back_populates="application", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (UniqueConstraint("application_id", "name", name="uq_service_per_app"),)

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(255), index=True)
    application_id = mapped_column(ForeignKey("applications.id"))

    application = relationship("Application", back_populates="services")
    versions = relationship("SchemaVersion", back_populates="service", cascade="all, delete-orphan")


class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    __table_args__ = (
        UniqueConstraint("application_id", "service_id", "version", name="uq_version_per_target"),
    )

    id = mapped_column(Integer, primary_key=True)
    application_id = mapped_column(ForeignKey("applications.id"))
    service_id = mapped_column(ForeignKey("services.id"), nullable=True)

    version = mapped_column(Integer, index=True)
    path = mapped_column(Text)
    media_type = mapped_column(String(64))
    checksum = mapped_column(String(128))
    uploaded_at = mapped_column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="versions")
    service = relationship("Service", back_populates="versions")
