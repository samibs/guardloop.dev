"""Conversation Management for Guardrail v2

Maintains conversation history for interactive sessions.
Enables proper context passing to LLM for Q&A flow.
"""

import uuid
from datetime import datetime
from typing import List, Optional

import structlog
from sqlalchemy.orm import Session

from guardrail.utils.db import ConversationHistoryModel

logger = structlog.get_logger(__name__)


class Message:
    """Conversation message"""

    def __init__(self, role: str, content: str, tokens_used: int = 0):
        self.role = role  # user, assistant, system
        self.content = content
        self.tokens_used = tokens_used
        self.timestamp = datetime.utcnow()


class ConversationManager:
    """Manage conversation history for interactive sessions"""

    def __init__(
        self,
        db_session: Session,
        max_context_tokens: int = 8000,
        max_turns: int = 20,
    ):
        """Initialize conversation manager

        Args:
            db_session: Database session
            max_context_tokens: Maximum tokens to keep in context
            max_turns: Maximum conversation turns to keep
        """
        self.session = db_session
        self.max_context_tokens = max_context_tokens
        self.max_turns = max_turns
        self.conversations = {}  # session_id -> List[Message]

    def start_conversation(self, session_id: Optional[str] = None) -> str:
        """Start new conversation

        Args:
            session_id: Optional session ID (generates new if None)

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        self.conversations[session_id] = []

        logger.info("Conversation started", session_id=session_id)
        return session_id

    def add_message(
        self, session_id: str, role: str, content: str, tokens_used: int = 0
    ) -> None:
        """Add message to conversation

        Args:
            session_id: Conversation session ID
            role: Message role (user, assistant, system)
            content: Message content
            tokens_used: Estimated tokens used
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        message = Message(role, content, tokens_used)
        self.conversations[session_id].append(message)

        # Save to database
        turn_number = len(self.conversations[session_id]) - 1

        db_message = ConversationHistoryModel(
            session_id=session_id,
            turn_number=turn_number,
            role=role,
            content=content,
            timestamp=message.timestamp,
            tokens_used=tokens_used,
        )

        self.session.add(db_message)
        self.session.commit()

        logger.debug(
            "Message added",
            session_id=session_id,
            role=role,
            turn=turn_number,
            tokens=tokens_used,
        )

    def get_history(
        self, session_id: str, include_system: bool = False
    ) -> List[Message]:
        """Get conversation history

        Args:
            session_id: Conversation session ID
            include_system: Include system messages

        Returns:
            List of messages
        """
        if session_id not in self.conversations:
            # Load from database
            self._load_from_db(session_id)

        messages = self.conversations.get(session_id, [])

        if not include_system:
            messages = [m for m in messages if m.role != "system"]

        return messages

    def build_context(
        self, session_id: str, current_prompt: str
    ) -> str:
        """Build conversation context for LLM

        Args:
            session_id: Conversation session ID
            current_prompt: Current user prompt

        Returns:
            Formatted context string
        """
        history = self.get_history(session_id, include_system=False)

        # Prune history if needed
        history = self._prune_history(history)

        if not history:
            return current_prompt

        # Format for LLM
        lines = ["# Conversation History\n"]

        for msg in history:
            role_prefix = "User:" if msg.role == "user" else "Assistant:"
            lines.append(f"{role_prefix} {msg.content}\n")

        lines.append(f"\n# Current Request\nUser: {current_prompt}")

        context = "\n".join(lines)

        logger.debug(
            "Context built",
            session_id=session_id,
            history_turns=len(history),
            total_length=len(context),
        )

        return context

    def clear_conversation(self, session_id: str) -> None:
        """Clear conversation history

        Args:
            session_id: Conversation session ID
        """
        if session_id in self.conversations:
            del self.conversations[session_id]

        logger.info("Conversation cleared", session_id=session_id)

    def get_active_sessions(self) -> List[str]:
        """Get list of active conversation sessions

        Returns:
            List of session IDs
        """
        return list(self.conversations.keys())

    def _load_from_db(self, session_id: str) -> None:
        """Load conversation history from database

        Args:
            session_id: Conversation session ID
        """
        messages_db = (
            self.session.query(ConversationHistoryModel)
            .filter(ConversationHistoryModel.session_id == session_id)
            .order_by(ConversationHistoryModel.turn_number)
            .all()
        )

        self.conversations[session_id] = [
            Message(m.role, m.content, m.tokens_used) for m in messages_db
        ]

        logger.debug(
            "Conversation loaded from DB", session_id=session_id, messages=len(messages_db)
        )

    def _prune_history(self, messages: List[Message]) -> List[Message]:
        """Prune conversation history to fit token/turn limits

        Args:
            messages: List of messages

        Returns:
            Pruned list of messages
        """
        # Check turn limit
        if len(messages) > self.max_turns:
            messages = messages[-self.max_turns :]
            logger.debug("Pruned by turn limit", kept=len(messages))

        # Check token limit
        total_tokens = sum(m.tokens_used for m in messages)

        if total_tokens > self.max_context_tokens:
            # Remove oldest messages until under limit
            while messages and total_tokens > self.max_context_tokens:
                removed = messages.pop(0)
                total_tokens -= removed.tokens_used

            logger.debug(
                "Pruned by token limit", kept=len(messages), total_tokens=total_tokens
            )

        return messages

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token
        return len(text) // 4

    def get_conversation_summary(self, session_id: str) -> dict:
        """Get conversation summary

        Args:
            session_id: Conversation session ID

        Returns:
            Summary dictionary
        """
        history = self.get_history(session_id, include_system=True)

        user_messages = [m for m in history if m.role == "user"]
        assistant_messages = [m for m in history if m.role == "assistant"]
        total_tokens = sum(m.tokens_used for m in history)

        return {
            "session_id": session_id,
            "total_turns": len(history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "total_tokens": total_tokens,
            "started_at": history[0].timestamp if history else None,
            "last_activity": history[-1].timestamp if history else None,
        }
