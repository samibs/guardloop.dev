-- Guardrail.dev Database Schema
-- SQLite Database for AI Safety Layer

-- Sessions table: Track all AI interactions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tool TEXT NOT NULL CHECK(tool IN ('claude', 'gemini', 'codex')),
    agent TEXT NOT NULL,
    mode TEXT NOT NULL CHECK(mode IN ('standard', 'strict')),
    prompt TEXT NOT NULL,
    enhanced_prompt TEXT,
    raw_output TEXT,
    parsed_output JSON,
    violations JSON,
    approved BOOLEAN DEFAULT 0,
    execution_time_ms INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sessions table
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON sessions(timestamp);
CREATE INDEX IF NOT EXISTS idx_sessions_tool ON sessions(tool);
CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent);
CREATE INDEX IF NOT EXISTS idx_sessions_mode ON sessions(mode);
CREATE INDEX IF NOT EXISTS idx_sessions_approved ON sessions(approved);

-- Failure modes table: Track AI failures
CREATE TABLE IF NOT EXISTS failure_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    tool TEXT NOT NULL CHECK(tool IN ('claude', 'gemini', 'codex')),
    category TEXT NOT NULL,
    pattern TEXT NOT NULL,
    issue TEXT NOT NULL,
    context TEXT,
    log_file TEXT,
    severity TEXT NOT NULL CHECK(severity IN ('low', 'medium', 'high', 'critical')),
    resolved BOOLEAN DEFAULT 0,
    resolution_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Indexes for failure_modes table
CREATE INDEX IF NOT EXISTS idx_failure_modes_timestamp ON failure_modes(timestamp);
CREATE INDEX IF NOT EXISTS idx_failure_modes_session_id ON failure_modes(session_id);
CREATE INDEX IF NOT EXISTS idx_failure_modes_tool ON failure_modes(tool);
CREATE INDEX IF NOT EXISTS idx_failure_modes_category ON failure_modes(category);
CREATE INDEX IF NOT EXISTS idx_failure_modes_severity ON failure_modes(severity);
CREATE INDEX IF NOT EXISTS idx_failure_modes_resolved ON failure_modes(resolved);

-- Violations table: Track guardrail violations
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    guardrail_type TEXT NOT NULL CHECK(guardrail_type IN ('bpsbs', 'ai', 'ux_ui', 'agent')),
    rule_violated TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('low', 'medium', 'high', 'critical')),
    suggestion TEXT,
    auto_fixed BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Indexes for violations table
CREATE INDEX IF NOT EXISTS idx_violations_session_id ON violations(session_id);
CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_violations_guardrail_type ON violations(guardrail_type);
CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity);
CREATE INDEX IF NOT EXISTS idx_violations_auto_fixed ON violations(auto_fixed);

-- Metrics table: Aggregated metrics
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    total_sessions INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    avg_execution_time_ms INTEGER DEFAULT 0,
    top_violations JSON,
    top_failures JSON,
    agent_stats JSON,
    tool_stats JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for metrics table
CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(date);

-- Guardrail versions table: Track guardrail document changes
CREATE TABLE IF NOT EXISTS guardrail_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    changes TEXT,
    author TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for guardrail_versions table
CREATE INDEX IF NOT EXISTS idx_guardrail_versions_timestamp ON guardrail_versions(timestamp);
CREATE INDEX IF NOT EXISTS idx_guardrail_versions_file_path ON guardrail_versions(file_path);
CREATE INDEX IF NOT EXISTS idx_guardrail_versions_version ON guardrail_versions(version);

-- Agent activity table: Track agent usage and performance
CREATE TABLE IF NOT EXISTS agent_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    agent TEXT NOT NULL,
    action TEXT NOT NULL,
    session_id TEXT,
    success BOOLEAN DEFAULT 1,
    execution_time_ms INTEGER,
    error_message TEXT,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Indexes for agent_activity table
CREATE INDEX IF NOT EXISTS idx_agent_activity_timestamp ON agent_activity(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_activity_agent ON agent_activity(agent);
CREATE INDEX IF NOT EXISTS idx_agent_activity_session_id ON agent_activity(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_activity_success ON agent_activity(success);

-- Context tracking table: Track context management
CREATE TABLE IF NOT EXISTS context_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    context_type TEXT NOT NULL CHECK(context_type IN ('file', 'directory', 'project', 'custom')),
    context_data JSON NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Index for context_tracking table
CREATE INDEX IF NOT EXISTS idx_context_tracking_session_id ON context_tracking(session_id);
CREATE INDEX IF NOT EXISTS idx_context_tracking_timestamp ON context_tracking(timestamp);
CREATE INDEX IF NOT EXISTS idx_context_tracking_context_type ON context_tracking(context_type);

-- Triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_sessions_timestamp
    AFTER UPDATE ON sessions
    FOR EACH ROW
    BEGIN
        UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_metrics_timestamp
    AFTER UPDATE ON metrics
    FOR EACH ROW
    BEGIN
        UPDATE metrics SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Views for common queries
CREATE VIEW IF NOT EXISTS v_recent_sessions AS
SELECT
    s.id,
    s.session_id,
    s.timestamp,
    s.tool,
    s.agent,
    s.mode,
    s.approved,
    s.execution_time_ms,
    COUNT(v.id) as violation_count
FROM sessions s
LEFT JOIN violations v ON s.id = v.session_id
GROUP BY s.id
ORDER BY s.timestamp DESC
LIMIT 100;

CREATE VIEW IF NOT EXISTS v_failure_summary AS
SELECT
    DATE(timestamp) as date,
    tool,
    category,
    severity,
    COUNT(*) as count
FROM failure_modes
GROUP BY DATE(timestamp), tool, category, severity
ORDER BY date DESC, count DESC;

CREATE VIEW IF NOT EXISTS v_violation_summary AS
SELECT
    DATE(timestamp) as date,
    guardrail_type,
    rule_violated,
    severity,
    COUNT(*) as count
FROM violations
GROUP BY DATE(timestamp), guardrail_type, rule_violated, severity
ORDER BY date DESC, count DESC;

CREATE VIEW IF NOT EXISTS v_agent_performance AS
SELECT
    agent,
    COUNT(*) as total_actions,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_actions,
    ROUND(AVG(execution_time_ms), 2) as avg_execution_time_ms,
    DATE(timestamp) as date
FROM agent_activity
GROUP BY agent, DATE(timestamp)
ORDER BY date DESC, agent;
