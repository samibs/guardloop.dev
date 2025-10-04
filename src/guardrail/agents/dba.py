"""DBA agent for database design validation"""

from guardrail.agents.base import AgentContext, AgentDecision, BaseAgent
from guardrail.utils.config import Config


class DBAAgent(BaseAgent):
    """DBA - Database architecture and schema validation"""

    def __init__(self, config: Config):
        super().__init__("dba", "~/.guardrail/guardrails/agents/dba.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        approved = True
        total_checks = 4
        issues_count = 0

        # Check for proper indexing
        if not self._has_indexes(context):
            issues_count += 1
            suggestions.append("Add indexes for query optimization on frequently accessed columns")

        # Check for migrations
        if not self._has_migrations(context):
            issues_count += 1
            suggestions.append("Include database migration scripts for schema changes")

        # Check for relationships
        if not self._has_relationships(context):
            issues_count += 1
            suggestions.append("Define foreign key relationships and constraints")

        # Check for data validation
        if not self._has_constraints(context):
            issues_count += 1
            suggestions.append("Add constraints: NOT NULL, UNIQUE, CHECK constraints")

        next_agent = "coder" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Database design validated" if approved else "Database design incomplete",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_indexes(self, context):
        return self._contains_keywords(
            context.raw_output, ["index", "create index", "idx_", "indexed"]
        )

    def _has_migrations(self, context):
        return self._contains_keywords(
            context.raw_output, ["migration", "alembic", "migrate", "schema change"]
        )

    def _has_relationships(self, context):
        return self._contains_keywords(
            context.raw_output, ["foreign key", "references", "relationship", "join"]
        )

    def _has_constraints(self, context):
        return self._contains_keywords(
            context.raw_output, ["not null", "unique", "check", "constraint", "primary key"]
        )
