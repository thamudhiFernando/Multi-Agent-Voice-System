from collections import defaultdict
from datetime import timedelta, datetime
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.core.logs import get_logger
from app.database.database import get_db
from app.database.models import ConversationHistory


logger = get_logger()


class ConversationService:
    """
    Service for managing conversation context and history.
    Stores recent messages in memory for quick access.
    """

    def __init__(self):
        """Initialize conversation service with in-memory storage"""
        # Store conversations in memory: {session_id: [messages]}
        self.conversations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Store last activity time: {session_id: datetime}
        self.last_activity: Dict[str, datetime] = {}

        logger.info("Conversation service initialized")

    def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a message to conversation history.

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            agent_type: Type of agent that generated the response
            metadata: Additional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "agent_type": agent_type,
            "metadata": metadata or {}
        }

        self.conversations[session_id].append(message)

        # Keep only the last N messages to manage memory
        if len(self.conversations[session_id]) > settings.MAX_CONVERSATION_HISTORY * 2:
            self.conversations[session_id] = self.conversations[session_id][-settings.MAX_CONVERSATION_HISTORY * 2:]

        # Update last activity time
        self.last_activity[session_id] = datetime.now()

        logger.debug(f"Added message to session {session_id}: {role}")

    async def persist_conversation(
        self,
        session_id: str,
        user_message: str,
        agent_response: str,
        agent_type: str,
        intent_detected: Optional[str] = None,
        confidence_score: Optional[float] = None,
        sentiment_score: Optional[float] = None,
        sentiment_label: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Persist conversation to database for long-term storage and analytics.

        Args:
            session_id: Session identifier
            user_message: User's message
            agent_response: Agent's response
            agent_type: Type of agent that handled the request
            intent_detected: Detected intent
            confidence_score: Classification confidence
            sentiment_score: Sentiment score
            sentiment_label: Sentiment label (positive, negative, neutral)
            response_time_ms: Response time in milliseconds
            extra_metadata: Additional metadata
        """
        try:
            async for session in get_db():
                conversation_entry = ConversationHistory(
                    session_id=session_id,
                    user_message=user_message,
                    agent_response=agent_response,
                    agent_type=agent_type,
                    intent_detected=intent_detected,
                    confidence_score=confidence_score,
                    sentiment_score=sentiment_score,
                    sentiment_label=sentiment_label,
                    response_time_ms=response_time_ms,
                    extra_metadata=extra_metadata or {}
                )

                session.add(conversation_entry)
                await session.commit()

                logger.debug(f"Persisted conversation for session {session_id} to database")

        except Exception as e:
            logger.error(f"Error persisting conversation to database: {e}")

    def get_conversation_history(
        self,
        session_id: str,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            max_messages: Maximum number of messages to return

        Returns:
            List of conversation messages
        """
        messages = self.conversations.get(session_id, [])

        if max_messages:
            messages = messages[-max_messages:]

        return messages

    def get_conversation_context_for_agent(
        self,
        session_id: str,
        max_turns: int = 5
    ) -> str:
        """
        Get formatted conversation context for agent prompts.

        Args:
            session_id: Session identifier
            max_turns: Maximum number of conversation turns to include

        Returns:
            Formatted context string
        """
        messages = self.get_conversation_history(session_id, max_messages=max_turns * 2)

        if not messages:
            return ""

        context_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            agent_type = msg.get("agent_type")

            if role == "user":
                context_parts.append(f"User: {content}")
            elif role == "assistant":
                agent_label = f" ({agent_type})" if agent_type else ""
                context_parts.append(f"Assistant{agent_label}: {content}")

        return "\n".join(context_parts)

    def get_last_user_message(self, session_id: str) -> Optional[str]:
        """
        Get the last user message from a session.

        Args:
            session_id: Session identifier

        Returns:
            Last user message content or None
        """
        messages = self.conversations.get(session_id, [])

        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content")

        return None

    def clear_session(self, session_id: str):
        """
        Clear conversation history for a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
        if session_id in self.last_activity:
            del self.last_activity[session_id]

        logger.info(f"Cleared session: {session_id}")

    def cleanup_expired_sessions(self):
        """
        Clean up sessions that have been inactive for too long.
        Should be called periodically.
        """
        timeout = timedelta(minutes=settings.CONVERSATION_TIMEOUT_MINUTES)
        now = datetime.now()

        expired_sessions = [
            session_id
            for session_id, last_time in self.last_activity.items()
            if now - last_time > timeout
        ]

        for session_id in expired_sessions:
            self.clear_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session statistics
        """
        messages = self.conversations.get(session_id, [])
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        # Count agent types used
        agent_types = defaultdict(int)
        for msg in assistant_messages:
            agent_type = msg.get("agent_type")
            if agent_type:
                agent_types[agent_type] += 1

        return {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "agents_used": dict(agent_types),
            "last_activity": self.last_activity.get(session_id).isoformat() if session_id in self.last_activity else None
        }


# Global conversation service instance
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """
    Get or create the global conversation service instance.

    Returns:
        ConversationService: Global conversation service instance
    """
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service