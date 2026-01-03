import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select

from app.core.logs import get_logger
from app.database.database import get_db
from app.database.models import SupportTicket

logger = get_logger()


class HumanEscalationService:
    """
    Service for managing human escalation and support ticket creation.
    Handles cases that require human intervention.
    """

    async def create_support_ticket(
        self,
        session_id: str,
        customer_email: Optional[str],
        issue_type: str,
        description: str,
        priority: str = "medium",
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a support ticket for human intervention.

        Args:
            session_id: Session identifier
            customer_email: Customer email address
            issue_type: Type of issue (technical, order, complaint, etc.)
            description: Detailed description of the issue
            priority: Ticket priority (low, medium, high, urgent)
            extra_metadata: Additional metadata

        Returns:
            ticket_id: Generated ticket ID
        """
        try:
            ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

            async for session in get_db():
                support_ticket = SupportTicket(
                    ticket_id=ticket_id,
                    session_id=session_id,
                    customer_email=customer_email,
                    issue_type=issue_type,
                    priority=priority,
                    status="open",
                    description=description,
                    extra_metadata=extra_metadata or {}
                )

                session.add(support_ticket)
                await session.commit()

                logger.info(f"Created support ticket {ticket_id} for session {session_id} with priority {priority}")

                return ticket_id

        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            raise

    async def should_escalate_to_customer(
        self,
        sentiment_analysis: Dict[str, Any],
        conversation_length: int
    ) -> tuple[bool, str, str]:
        """
        Determine if conversation should be escalated to human support.

        Args:
            sentiment_analysis: Sentiment analysis results
            conversation_length: Number of messages in conversation

        Returns:
            Tuple of (should_escalate, reason, priority)
        """
        should_escalate = False
        reason = ""
        priority = "medium"

        # Check for explicit escalation flag
        if sentiment_analysis.get("requires_human_escalation", False):
            should_escalate = True
            reason = "Customer frustration or urgent issue detected"
            priority = "high"

        # Check for high frustration
        elif sentiment_analysis.get("is_frustrated", False):
            should_escalate = True
            reason = "Customer frustration detected"
            priority = "high"

        # Check for very negative sentiment
        elif sentiment_analysis.get("is_negative", False) and sentiment_analysis.get("score", 0) < -0.7:
            should_escalate = True
            reason = "Very negative sentiment detected"
            priority = "high"

        # Check for long unresolved conversation
        elif conversation_length > 10:
            should_escalate = True
            reason = "Extended conversation without resolution"
            priority = "medium"

        # Check for urgent issues
        elif sentiment_analysis.get("is_urgent", False) and sentiment_analysis.get("urgency_score", 0) > 0.8:
            should_escalate = True
            reason = "Urgent issue requires immediate attention"
            priority = "urgent"

        return should_escalate, reason, priority

    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve support ticket by ID.

        Args:
            ticket_id: Ticket identifier

        Returns:
            Ticket data or None
        """
        try:
            async for session in get_db():
                query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)
                result = await session.execute(query)
                ticket = result.scalar_one_or_none()

                if ticket:
                    return {
                        "ticket_id": ticket.ticket_id,
                        "session_id": ticket.session_id,
                        "created_at": ticket.created_at.isoformat(),
                        "customer_email": ticket.customer_email,
                        "issue_type": ticket.issue_type,
                        "priority": ticket.priority,
                        "status": ticket.status,
                        "description": ticket.description,
                        "resolution": ticket.resolution,
                        "assigned_agent": ticket.assigned_agent,
                        "extra_metadata": ticket.extra_metadata
                    }

                return None

        except Exception as e:
            logger.error(f"Error retrieving ticket: {e}")
            return None

    async def get_tickets_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all support tickets for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of tickets
        """
        try:
            async for session in get_db():
                query = select(SupportTicket).where(
                    SupportTicket.session_id == session_id
                ).order_by(SupportTicket.created_at.desc())

                result = await session.execute(query)
                tickets = result.scalars().all()

                return [
                    {
                        "ticket_id": ticket.ticket_id,
                        "created_at": ticket.created_at.isoformat(),
                        "issue_type": ticket.issue_type,
                        "priority": ticket.priority,
                        "status": ticket.status,
                        "description": ticket.description
                    }
                    for ticket in tickets
                ]

        except Exception as e:
            logger.error(f"Error retrieving tickets for session: {e}")
            return []

    async def update_ticket_status(
        self,
        ticket_id: str,
        status: str,
        resolution: Optional[str] = None,
        assigned_agent: Optional[str] = None
    ):
        """
        Update support ticket status.

        Args:
            ticket_id: Ticket identifier
            status: New status (open, in_progress, resolved, closed)
            resolution: Resolution notes
            assigned_agent: Assigned human agent
        """
        try:
            async for session in get_db():
                query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)
                result = await session.execute(query)
                ticket = result.scalar_one_or_none()

                if ticket:
                    ticket.status = status
                    if resolution:
                        ticket.resolution = resolution
                    if assigned_agent:
                        ticket.assigned_agent = assigned_agent
                    ticket.updated_at = datetime.now()

                    await session.commit()

                    logger.info(f"Updated ticket {ticket_id} status to {status}")

        except Exception as e:
            logger.error(f"Error updating ticket status: {e}")
            raise


# Global escalation service instance
_escalation_service: Optional[HumanEscalationService] = None


def get_escalation_service() -> HumanEscalationService:
    """
    Get or create the global escalation service instance.

    Returns:
        HumanEscalationService: Global escalation service instance
    """
    global _escalation_service
    if _escalation_service is None:
        _escalation_service = HumanEscalationService()
    return _escalation_service
