"""Database models and utilities for guardrail.dev"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.types import JSON, TypeDecorator

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type using UUID."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return str(uuid.UUID(value))

    def process_result_value(self, value: Any, dialect: Any) -> Optional[uuid.UUID]:
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class SessionModel(Base):
    """AI interaction session model"""

    __tablename__ = "sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    tool = Column(String(20), nullable=False, index=True)
    agent = Column(String(50), nullable=False, index=True)
    mode = Column(String(20), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    enhanced_prompt = Column(Text)
    raw_output = Column(Text)
    parsed_output = Column(JSON)
    violations = Column(JSON)
    approved = Column(Boolean, default=False, index=True)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    failure_modes = relationship("FailureModeModel", back_populates="session")
    violations_rel = relationship("ViolationModel", back_populates="session")
    agent_activities = relationship("AgentActivityModel", back_populates="session")
    context_tracking = relationship("ContextTrackingModel", back_populates="session")

    __table_args__ = (
        CheckConstraint(tool.in_(["claude", "gemini", "codex"]), name="check_tool"),
        CheckConstraint(mode.in_(["standard", "strict"]), name="check_mode"),
    )


class FailureModeModel(Base):
    """AI failure tracking model"""

    __tablename__ = "failure_modes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    session_id = Column(GUID, ForeignKey("sessions.id"), index=True)
    tool = Column(String(20), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    pattern = Column(String(200), nullable=False)
    issue = Column(Text, nullable=False)
    context = Column(Text)
    log_file = Column(String(500))
    severity = Column(String(20), nullable=False, index=True)
    resolved = Column(Boolean, default=False, index=True)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="failure_modes")

    __table_args__ = (
        CheckConstraint(tool.in_(["claude", "gemini", "codex"]), name="check_tool"),
        CheckConstraint(
            severity.in_(["low", "medium", "high", "critical"]), name="check_severity"
        ),
    )


class ViolationModel(Base):
    """Guardrail violation model"""

    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(GUID, ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    guardrail_type = Column(String(20), nullable=False, index=True)
    rule_violated = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    suggestion = Column(Text)
    auto_fixed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="violations_rel")

    __table_args__ = (
        CheckConstraint(
            guardrail_type.in_(["bpsbs", "ai", "ux_ui", "agent"]),
            name="check_guardrail_type",
        ),
        CheckConstraint(
            severity.in_(["low", "medium", "high", "critical"]), name="check_severity"
        ),
    )


class MetricModel(Base):
    """Aggregated metrics model"""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    total_sessions = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_execution_time_ms = Column(Integer, default=0)
    top_violations = Column(JSON)
    top_failures = Column(JSON)
    agent_stats = Column(JSON)
    tool_stats = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GuardrailVersionModel(Base):
    """Guardrail document version tracking model"""

    __tablename__ = "guardrail_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    file_path = Column(String(500), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False)
    changes = Column(Text)
    author = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentActivityModel(Base):
    """Agent activity tracking model"""

    __tablename__ = "agent_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    agent = Column(String(50), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    session_id = Column(GUID, ForeignKey("sessions.id"), index=True)
    success = Column(Boolean, default=True, index=True)
    execution_time_ms = Column(Integer)
    error_message = Column(Text)
    agent_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="agent_activities")


class ContextTrackingModel(Base):
    """Context management tracking model"""

    __tablename__ = "context_tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(GUID, ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    context_type = Column(String(20), nullable=False, index=True)
    context_data = Column(JSON, nullable=False)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="context_tracking")

    __table_args__ = (
        CheckConstraint(
            context_type.in_(["file", "directory", "project", "custom"]),
            name="check_context_type",
        ),
    )


class DatabaseManager:
    """Database management utilities"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def init_db(self) -> None:
        """Initialize database with schema"""
        Base.metadata.create_all(bind=self.engine)

        # Load SQL schema for views and triggers
        schema_path = Path(__file__).parent.parent.parent.parent / "data" / "schema.sql"
        if schema_path.exists():
            with open(schema_path) as f:
                schema_sql = f.read()
                # Split by statements and execute
                statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
                with self.engine.connect() as conn:
                    for statement in statements:
                        if statement:
                            conn.execute(statement)
                    conn.commit()

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def backup_db(self, backup_path: Optional[str] = None) -> str:
        """Create database backup"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = str(self.db_path.parent / f"guardrail_backup_{timestamp}.db")

        import shutil

        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_session() as session:
            stats = {
                "total_sessions": session.query(SessionModel).count(),
                "total_failures": session.query(FailureModeModel).count(),
                "total_violations": session.query(ViolationModel).count(),
                "total_agents_activity": session.query(AgentActivityModel).count(),
                "db_size_mb": self.db_path.stat().st_size / (1024 * 1024),
            }
            return stats
