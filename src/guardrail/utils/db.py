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
    text,
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


# ============================================================================
# Version 2 Models - Adaptive Learning System
# ============================================================================


class LearnedPatternModel(Base):
    """Learned failure patterns from LLM interactions"""

    __tablename__ = "learned_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_hash = Column(String(64), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    signature = Column(Text, nullable=False)
    description = Column(Text)
    frequency = Column(Integer, default=1, index=True)
    severity = Column(String(20), nullable=False, index=True)
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    confidence_score = Column(Float, default=0.0, index=True)
    example_sessions = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dynamic_guardrails = relationship("DynamicGuardrailModel", back_populates="pattern")

    __table_args__ = (
        CheckConstraint(
            severity.in_(["low", "medium", "high", "critical"]), name="check_pattern_severity"
        ),
        Index("idx_pattern_category_severity", "category", "severity"),
        Index("idx_pattern_frequency", "frequency"),
    )


class DynamicGuardrailModel(Base):
    """Auto-generated guardrails from learned patterns"""

    __tablename__ = "dynamic_guardrails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(Integer, ForeignKey("learned_patterns.id"), nullable=False, index=True)
    rule_text = Column(Text, nullable=False)
    rule_category = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="trial", index=True)
    enforcement_mode = Column(String(20), nullable=False, default="warn", index=True)
    task_types = Column(JSON)  # Which task types this applies to
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, index=True)
    deactivated_at = Column(DateTime, index=True)
    created_by = Column(String(50), default="system")
    metadata = Column(JSON)

    # Relationships
    pattern = relationship("LearnedPatternModel", back_populates="dynamic_guardrails")
    effectiveness = relationship("RuleEffectivenessModel", back_populates="rule")

    __table_args__ = (
        CheckConstraint(
            status.in_(["trial", "validated", "enforced", "deprecated"]),
            name="check_rule_status",
        ),
        CheckConstraint(
            enforcement_mode.in_(["warn", "block", "auto_fix"]),
            name="check_enforcement_mode",
        ),
        Index("idx_guardrail_status_confidence", "status", "confidence"),
    )


class RuleEffectivenessModel(Base):
    """Track effectiveness of dynamic guardrails"""

    __tablename__ = "rule_effectiveness"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("dynamic_guardrails.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    prevented_failures = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    true_positives = Column(Integer, default=0)
    times_triggered = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    user_feedback = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rule = relationship("DynamicGuardrailModel", back_populates="effectiveness")

    __table_args__ = (
        Index("idx_effectiveness_date", "date"),
        Index("idx_effectiveness_rule_date", "rule_id", "date"),
    )


class ConversationHistoryModel(Base):
    """Conversation history for interactive sessions"""

    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(GUID, nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    tokens_used = Column(Integer, default=0)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            role.in_(["user", "assistant", "system"]),
            name="check_message_role",
        ),
        Index("idx_conversation_session_turn", "session_id", "turn_number"),
        Index("idx_conversation_timestamp", "timestamp"),
    )


class TaskClassificationModel(Base):
    """Task classification results for prompts"""

    __tablename__ = "task_classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(GUID, ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    task_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    requires_guardrails = Column(Boolean, default=True, index=True)
    classification_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            task_type.in_(["code", "content", "creative", "mixed", "unknown"]),
            name="check_task_type",
        ),
        Index("idx_classification_type_confidence", "task_type", "confidence"),
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

        # Note: Views and triggers from schema.sql are optional
        # SQLAlchemy models provide the core schema

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
