from crewai import Agent, Task, Crew

from app.agents.agent_tools import product_search_tool, promotion_search_tool, knowledge_base_search_tool, \
    order_lookup_tool
from app.core.config import settings
from app.core.logs import get_logger
from langchain_openai import ChatOpenAI

logger = get_logger()

class AgentFactory:
    """Factory class for creating CrewAI agents"""

    def __init__(self):
        """Initialize LLM instances for agents"""
        # Orchestrator uses lower temperature for more deterministic routing
        self.orchestrator_llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.ORCHESTRATOR_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )

        # Sub-agents use higher temperature for more creative responses
        self.agent_llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.SUB_AGENT_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def create_orchestrator_agent(self) -> Agent:
        """
        Create the orchestrator agent (router).
        Routes customer inquiries to appropriate specialized agents.
        """
        return Agent(
            role="Orchestrator Agent",
            goal="Analyze customer inquiries and route them to the most appropriate specialized agent based on intent and context",
            backstory="""You are the primary routing agent for ElectroMart's customer service system.
                Your expertise lies in understanding customer intent and determining which specialized agent
                can best handle their request. You excel at:
                - Intent classification (sales, support, orders, marketing, general service)
                - Context analysis from conversation history
                - Identifying urgent or complex cases that may need multiple agents
                - Providing seamless handoffs between agents when topics change

                You work with 5 specialized agents:
                1. Sales Agent - Product inquiries, pricing, availability, recommendations
                2. Marketing/Promotions Agent - Deals, discounts, loyalty programs, campaigns
                3. Technical Support Agent - Troubleshooting, repairs, warranty, technical specs
                4. Order & Logistics Agent - Order tracking, shipping, returns, refunds
                5. Customer Service Agent - General inquiries, store info, feedback, policies

                Your routing decisions should be confident and accurate, with >85% classification accuracy.""",
            llm=self.orchestrator_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )

    def create_sales_agent(self) -> Agent:
        """
        Create the Sales Agent.
        Handles product inquiries, pricing, availability, and recommendations.
        """
        return Agent(
            role="Sales Agent",
            goal="Assist customers with product inquiries, provide pricing information, check availability, and make personalized recommendations",
            backstory="""You are ElectroMart's expert sales consultant specializing in consumer electronics.
                You have deep product knowledge across phones, laptops, TVs, audio equipment, tablets, and accessories.

                Your strengths:
                - Product expertise: You know specifications, features, and use cases for all products
                - Comparison skills: You can compare products and highlight key differences
                - Personalization: You ask clarifying questions to understand customer needs
                - Upselling: You suggest complementary products and bundle deals when appropriate
                - Stock awareness: You always check and communicate current availability

                You provide responses that are:
                - Informative yet concise
                - Focused on customer needs and budget
                - Include specific product details (price, specs, availability)
                - Professional but friendly

                When customers ask about products, you use your tools to search the catalog and provide
                accurate, up-to-date information.""",
            tools=[product_search_tool, promotion_search_tool],
            llm=self.agent_llm,
            verbose=True,
            allow_delegation=False
        )

    def create_marketing_agent(self) -> Agent:
        """
        Create the Marketing/Promotions Agent.
        Handles deals, discounts, loyalty programs, and campaigns.
        """
        return Agent(
            role="Marketing and Promotions Agent",
            goal="Inform customers about current deals, promotions, discount codes, loyalty programs, and special offers",
            backstory="""You are ElectroMart's marketing specialist focused on helping customers save money
                and get the best value from their purchases.

                Your expertise includes:
                - Current promotions: You know all active sales, deals, and special offers
                - Discount codes: You can provide and explain promo codes and their requirements
                - Loyalty program: You explain ElectroMart Rewards benefits and how to join
                - Seasonal campaigns: You inform about upcoming sales and events
                - Eligibility: You help customers understand if they qualify for specific discounts

                You are enthusiastic about helping customers save money while maintaining professionalism.
                You always:
                - Provide specific promo codes when applicable
                - Explain any requirements or restrictions clearly
                - Suggest the best way to maximize savings
                - Highlight limited-time offers with appropriate urgency

                You use your tools to find relevant promotions based on customer interest.""",
            tools=[promotion_search_tool, product_search_tool],
            llm=self.agent_llm,
            verbose=True,
            allow_delegation=False
        )

    def create_technical_support_agent(self) -> Agent:
        """
        Create the Technical Support Agent.
        Handles troubleshooting, warranty, repairs, and technical specifications.
        """
        return Agent(
            role="Technical Support Agent",
            goal="Provide technical assistance, troubleshooting guidance, warranty information, and repair services",
            backstory="""You are ElectroMart's senior technical support specialist with expertise in
                diagnosing and resolving technical issues across all electronic devices.

                Your core competencies:
                - Troubleshooting: You provide step-by-step solutions for common technical problems
                - Warranty expertise: You know warranty policies, coverage, and claim procedures
                - Repair services: You explain repair options, timelines, and costs
                - Technical specs: You can explain technical specifications in user-friendly terms
                - Setup assistance: You guide customers through device setup and configuration

                Your approach:
                - Patient and empathetic with frustrated customers
                - Clear, sequential instructions for troubleshooting steps
                - Safety-first mindset for technical procedures
                - Honest about limitations and when professional service is needed
                - Document issues thoroughly for better resolution

                You search the technical support knowledge base for relevant troubleshooting guides
                and warranty information to provide accurate assistance.""",
            tools=[knowledge_base_search_tool, product_search_tool],
            llm=self.agent_llm,
            verbose=True,
            allow_delegation=False
        )

    def create_order_logistics_agent(self) -> Agent:
        """
        Create the Order & Logistics Agent.
        Handles order tracking, shipping, returns, and refunds.
        """
        return Agent(
            role="Order and Logistics Agent",
            goal="Assist customers with order tracking, shipping information, returns, exchanges, and refund processing",
            backstory="""You are ElectroMart's logistics coordinator specializing in order management
                and customer satisfaction through efficient delivery and returns processing.

                Your responsibilities:
                - Order tracking: Provide real-time status updates and delivery estimates
                - Shipping info: Explain shipping options, costs, and timelines
                - Returns: Guide customers through the return process and policies
                - Refunds: Explain refund timelines and processing
                - Address changes: Help with delivery address modifications when possible
                - Issue resolution: Handle shipping problems like delays or damaged packages

                Your communication style:
                - Clear and specific with order details and timelines
                - Proactive in providing tracking information
                - Empathetic when dealing with order issues or delays
                - Efficient in processing return requests
                - Detail-oriented with order numbers and tracking codes

                You use order lookup tools to provide accurate, real-time information and can
                search knowledge bases for return and shipping policies.""",
            tools=[order_lookup_tool, knowledge_base_search_tool],
            llm=self.agent_llm,
            verbose=True,
            allow_delegation=False
        )

    def create_customer_service_agent(self) -> Agent:
        """
        Create the Customer Service Agent (5th agent).
        Handles general inquiries, store information, policies, and feedback.
        """
        return Agent(
            role="Customer Service Agent",
            goal="Provide general customer service, store information, answer policy questions, and handle feedback",
            backstory="""You are ElectroMart's friendly customer service representative handling general
                inquiries and providing information about the company, stores, and policies.

                Your areas of expertise:
                - Store information: Hours, locations, services offered at stores
                - General policies: Return policies, price matching, warranties (overview level)
                - Account assistance: Help with account creation, password resets, profile updates
                - Feedback collection: Gather customer feedback and suggestions
                - General questions: Answer miscellaneous questions not covered by other agents
                - Escalation: Identify when to escalate to human representatives

                Your personality:
                - Warm and welcoming approach
                - Patient with all types of questions
                - Knowledgeable about company policies and procedures
                - Good at redirecting complex issues to specialized agents when needed
                - Excellent at making customers feel heard and valued

                You search knowledge bases for store information, policies, and general FAQs
                to provide accurate information.""",
            tools=[knowledge_base_search_tool, promotion_search_tool],
            llm=self.agent_llm,
            verbose=True,
            allow_delegation=False
        )


class AgentCoordinator:
    """
    Coordinates the multi-agent system.
    Routes customer queries to appropriate agents and manages responses.
    """

    def __init__(self):
        """Initialize agent coordinator with all agents"""
        self.factory = AgentFactory()

        # Create all agents
        self.orchestrator = self.factory.create_orchestrator_agent()
        self.sales_agent = self.factory.create_sales_agent()
        self.marketing_agent = self.factory.create_marketing_agent()
        self.technical_support_agent = self.factory.create_technical_support_agent()
        self.order_logistics_agent = self.factory.create_order_logistics_agent()
        self.customer_service_agent = self.factory.create_customer_service_agent()

        # Agent mapping for routing
        self.agent_map = {
            "sales": self.sales_agent,
            "marketing": self.marketing_agent,
            "technical_support": self.technical_support_agent,
            "order_logistics": self.order_logistics_agent,
            "customer_service": self.customer_service_agent
        }

        logger.info("Agent coordinator initialized with all agents")

    def classify_intent(self, message: str, conversation_context: str = "") -> tuple[str, float]:
        """
        Use orchestrator to classify intent and determine which agent to use.

        Args:
            message: User message
            conversation_context: Previous conversation context

        Returns:
            Tuple of (agent_type, confidence_score)
        """
        try:
            # Create classification task
            context_section = f"\n\nConversation Context:\n{conversation_context}" if conversation_context else ""

            classification_task = Task(
                description=f"""Analyze the following customer message and determine which specialized agent
                    should handle it. Consider the conversation context if provided.

                    Customer Message: "{message}"{context_section}

                    Available agents:
                    - sales: Product inquiries, pricing, availability, recommendations, comparisons
                    - marketing: Promotions, discounts, deals, loyalty program, coupon codes
                    - technical_support: Troubleshooting, repairs, warranty, technical issues, setup help
                    - order_logistics: Order tracking, shipping, returns, refunds, delivery questions
                    - customer_service: General inquiries, store info, policies, feedback, account help

                    Respond with ONLY the agent type (sales, marketing, technical_support, order_logistics, or customer_service)
                    and a confidence score between 0 and 1, separated by a comma.

                    Example response: "sales, 0.95" """,
                agent=self.orchestrator,
                expected_output="Agent type and confidence score (e.g., 'sales, 0.95')"
            )

            # Create crew for classification
            crew = Crew(
                agents=[self.orchestrator],
                tasks=[classification_task],
                verbose=False
            )

            # Execute classification
            result = crew.kickoff()

            # Parse result
            result_text = str(result).strip().lower()
            parts = result_text.split(',')

            if len(parts) >= 2:
                agent_type = parts[0].strip()
                try:
                    confidence = float(parts[1].strip())
                except ValueError:
                    confidence = 0.8  # Default confidence

                # Validate agent type
                if agent_type in self.agent_map:
                    logger.info(f"Intent classified: {agent_type} (confidence: {confidence})")
                    return agent_type, confidence

            # Fallback to customer service
            logger.warning(f"Could not parse classification result: {result_text}")
            return "customer_service", 0.5

        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            return "customer_service", 0.5

    def process_with_agent(
            self,
            agent_type: str,
            message: str,
            conversation_context: str = ""
    ) -> str:
        """
        Process message with specific specialized agent.

        Args:
            agent_type: Type of agent to use
            message: User message
            conversation_context: Previous conversation context

        Returns:
            Agent response
        """
        try:
            agent = self.agent_map.get(agent_type)
            if not agent:
                logger.error(f"Agent type '{agent_type}' not found")
                return "I apologize, but I'm having trouble processing your request. Please try again."

            # Create context section
            context_section = f"\n\nPrevious conversation context:\n{conversation_context}" if conversation_context else ""

            # Create task for the specialized agent
            task = Task(
                description=f"""Handle the following customer inquiry:

                    Customer Message: "{message}"{context_section}

                    Provide a helpful, accurate, and professional response. Use your tools to search for
                    relevant information when needed. Keep your response concise but complete.""",
                agent=agent,
                expected_output="Helpful response to customer inquiry"
            )

            # Create crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )

            # Execute task
            result = crew.kickoff()

            logger.info(f"Agent {agent_type} processed message successfully")
            return str(result)

        except Exception as e:
            logger.error(f"Error processing with agent {agent_type}: {e}")
            return "I apologize, but I encountered an error processing your request. Please try again or rephrase your question."


# Global agent coordinator instance
_agent_coordinator: AgentCoordinator = None


def get_agent_coordinator() -> AgentCoordinator:
    """
    Get or create the global agent coordinator instance.

    Returns:
        AgentCoordinator: Global agent coordinator
    """
    global _agent_coordinator
    if _agent_coordinator is None:
        _agent_coordinator = AgentCoordinator()
    return _agent_coordinator
