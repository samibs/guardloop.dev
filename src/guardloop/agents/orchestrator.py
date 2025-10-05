"""Orchestrator agent for routing and coordinating other agents"""

from typing import Dict, List, Optional

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.agents.chain_optimizer import AgentChainOptimizer
from guardloop.utils.config import Config


class OrchestratorAgent(BaseAgent):
    """Orchestrates agent workflow and routing"""

    def __init__(self, config: Config):
        """Initialize orchestrator

        Args:
            config: Guardrail configuration
        """
        super().__init__(
            "orchestrator", "~/.guardrail/guardrails/agents/orchestrator.md"
        )
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.chain_optimizer = AgentChainOptimizer()

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator

        Args:
            name: Agent name
            agent: Agent instance
        """
        self.agents[name] = agent

    async def load_agents(self) -> None:
        """Load all specialized agents"""
        from guardloop.agents.architect import ArchitectAgent
        from guardloop.agents.business_analyst import BusinessAnalystAgent
        from guardloop.agents.coder import CoderAgent
        from guardloop.agents.dba import DBAAgent
        from guardloop.agents.debug_hunter import DebugHunterAgent
        from guardloop.agents.documentation import DocumentationAgent
        from guardloop.agents.evaluator import EvaluatorAgent
        from guardloop.agents.secops import SecOpsAgent
        from guardloop.agents.sre import SREAgent
        from guardloop.agents.standards_oracle import StandardsOracleAgent
        from guardloop.agents.tester import TesterAgent
        from guardloop.agents.ux_designer import UXDesignerAgent

        self.agents = {
            "architect": ArchitectAgent(self.config),
            "business_analyst": BusinessAnalystAgent(self.config),
            "coder": CoderAgent(self.config),
            "dba": DBAAgent(self.config),
            "debug_hunter": DebugHunterAgent(self.config),
            "documentation": DocumentationAgent(self.config),
            "evaluator": EvaluatorAgent(self.config),
            "secops": SecOpsAgent(self.config),
            "sre": SREAgent(self.config),
            "standards_oracle": StandardsOracleAgent(self.config),
            "tester": TesterAgent(self.config),
            "ux_designer": UXDesignerAgent(self.config),
        }

    async def route(self, prompt: str) -> str:
        """Determine which agent should handle this prompt

        Args:
            prompt: User prompt

        Returns:
            Agent name to route to
        """
        # Keyword-based routing
        keywords = {
            "business_analyst": [
                "requirements",
                "feature",
                "story",
                "epic",
                "business",
                "user needs",
            ],
            "architect": [
                "design",
                "architecture",
                "system",
                "structure",
                "components",
                "layers",
            ],
            "ux_designer": [
                "ui",
                "ux",
                "interface",
                "user experience",
                "design system",
                "responsive",
            ],
            "dba": [
                "database",
                "schema",
                "migration",
                "sql",
                "table",
                "index",
                "query",
            ],
            "coder": [
                "implement",
                "code",
                "develop",
                "create",
                "function",
                "class",
                "method",
            ],
            "tester": [
                "test",
                "coverage",
                "verify",
                "e2e",
                "unit test",
                "integration",
            ],
            "debug_hunter": [
                "bug",
                "error",
                "fix",
                "debug",
                "issue",
                "crash",
                "exception",
            ],
            "secops": [
                "security",
                "vulnerability",
                "auth",
                "encryption",
                "xss",
                "injection",
            ],
            "sre": [
                "deploy",
                "monitor",
                "performance",
                "scale",
                "infrastructure",
                "kubernetes",
            ],
            "standards_oracle": [
                "standard",
                "convention",
                "style",
                "best practice",
                "guideline",
            ],
            "evaluator": ["review", "evaluate", "assess", "quality", "audit"],
            "documentation": [
                "document",
                "readme",
                "comment",
                "api doc",
                "guide",
                "tutorial",
            ],
        }

        prompt_lower = prompt.lower()

        # Score each agent based on keyword matches
        scores = {}
        for agent_name, agent_keywords in keywords.items():
            score = sum(
                1 for keyword in agent_keywords if keyword in prompt_lower
            )
            if score > 0:
                scores[agent_name] = score

        # Return agent with highest score
        if scores:
            return max(scores, key=scores.get)

        # Default to architect for design/planning tasks
        return "architect"

    async def orchestrate(
        self,
        context: AgentContext,
        task_type: str = "implement_function",
        mode: str = "standard",
        user_agent: Optional[str] = None,
    ) -> List[AgentDecision]:
        """Execute optimal agent chain

        Args:
            context: Agent context
            task_type: Type of task being performed
            mode: Operating mode (standard or strict)
            user_agent: User-specified agent (optional)

        Returns:
            List of agent decisions in execution order
        """
        # Get optimal chain from optimizer
        chain = self.chain_optimizer.select_chain(
            task_type=task_type, mode=mode, user_specified_agent=user_agent
        )

        # Log chain selection
        complexity = self.chain_optimizer.get_complexity(task_type)
        logger.info(
            f"Selected {len(chain)} agents for {complexity.value} task",
            agents=chain,
            task_type=task_type,
            mode=mode,
        )

        # Execute chain
        decisions = []
        for agent_name in chain:
            # Get agent (normalize name for lookup)
            if agent_name not in self.agents:
                logger.warning(f"Agent not registered: {agent_name}")
                continue

            agent = self.agents[agent_name]

            # Evaluate
            decision = await agent.evaluate(context)
            decisions.append(decision)

            # Stop if agent blocks
            if not decision.approved:
                logger.warning(
                    f"Chain stopped by {agent_name}", reason=decision.reason
                )
                break

            # Update context with findings
            context.violations.extend(decision.violations)

        return decisions

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        """Evaluate context (orchestrator doesn't evaluate directly)

        Args:
            context: Agent context

        Returns:
            Agent decision
        """
        # Orchestrator delegates to other agents
        decisions = await self.orchestrate(context)

        # Aggregate decisions
        all_approved = all(d.approved for d in decisions)
        all_suggestions = []
        for d in decisions:
            all_suggestions.extend(d.suggestions)

        return AgentDecision(
            agent_name=self.name,
            approved=all_approved,
            reason=f"Orchestrated {len(decisions)} agent(s)",
            suggestions=all_suggestions,
            confidence=sum(d.confidence for d in decisions) / len(decisions)
            if decisions
            else 1.0,
        )

    def get_agent_chain(self, start_agent: str) -> List[str]:
        """Get the default agent execution chain

        Args:
            start_agent: Starting agent

        Returns:
            List of agent names in chain
        """
        # Default chains based on agent type
        chains = {
            "business_analyst": ["business_analyst", "architect", "evaluator"],
            "architect": ["architect", "dba", "coder", "tester", "evaluator"],
            "ux_designer": ["ux_designer", "coder", "tester", "evaluator"],
            "dba": ["dba", "coder", "tester", "evaluator"],
            "coder": ["coder", "tester", "secops", "evaluator"],
            "tester": ["tester", "secops", "evaluator"],
            "debug_hunter": ["debug_hunter", "tester", "evaluator"],
            "secops": ["secops", "sre", "evaluator"],
            "sre": ["sre", "evaluator"],
            "standards_oracle": ["standards_oracle", "evaluator"],
            "documentation": ["documentation", "evaluator"],
        }

        return chains.get(start_agent, [start_agent, "evaluator"])

    def get_stats(self) -> Dict:
        """Get orchestrator statistics

        Returns:
            Statistics dictionary
        """
        return {
            "registered_agents": len(self.agents),
            "agent_names": list(self.agents.keys()),
        }
