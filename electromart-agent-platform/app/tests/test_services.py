import pytest

from app.services.conversation_service import ConversationService
from app.services.data_service import DataService
from app.services.sentiment_service import SentimentService


class TestDataService:
    def setup_method(self):
        """Setup test fixtures"""
        self.data_service = DataService()

    def test_get_all_products(self):
        """Test retrieving all products"""
        products = self.data_service.get_all_products()
        assert len(products) > 0
        assert all('id' in p for p in products)
        assert all('name' in p for p in products)
        assert all('price' in p for p in products)

    def test_get_product_by_id(self):
        """Test retrieving product by ID"""
        product = self.data_service.get_product_by_id("PROD001")
        assert product is not None
        assert product['id'] == "PROD001"
        assert 'name' in product
        assert 'price' in product

    def test_get_product_by_invalid_id(self):
        """Test retrieving product with invalid ID"""
        product = self.data_service.get_product_by_id("INVALID_ID")
        assert product is None

    def test_search_products_by_query(self):
        """Test searching products by query"""
        products = self.data_service.search_products(query="iphone")
        assert len(products) > 0
        assert any('iphone' in p['name'].lower() for p in products)

    def test_search_products_by_category(self):
        """Test searching products by category"""
        products = self.data_service.search_products(category="Phones")
        assert len(products) > 0
        assert all(p['category'] == 'Phones' for p in products)

    def test_search_products_by_price_range(self):
        """Test searching products by price range"""
        products = self.data_service.search_products(min_price=500, max_price=1000)
        assert len(products) > 0
        assert all(500 <= p['price'] <= 1000 for p in products)

    def test_get_order_by_id(self):
        """Test retrieving order by ID"""
        order = self.data_service.get_order_by_id("ORD12345")
        assert order is not None
        assert order['order_id'] == "ORD12345"
        assert 'customer_email' in order
        assert 'items' in order

    def test_get_all_promotions(self):
        """Test retrieving all promotions"""
        promotions = self.data_service.get_all_promotions()
        assert len(promotions) > 0
        assert all('code' in p for p in promotions)

    def test_get_active_promotions_only(self):
        """Test retrieving only active promotions"""
        promotions = self.data_service.get_all_promotions(active_only=True)
        assert len(promotions) > 0
        assert all(p['status'] == 'active' for p in promotions)

    def test_get_promotion_by_code(self):
        """Test retrieving promotion by code"""
        promotion = self.data_service.get_promotion_by_code("NEWYEAR30")
        assert promotion is not None
        assert promotion['code'] == "NEWYEAR30"

    def test_search_knowledge_base(self):
        """Test searching knowledge base"""
        results = self.data_service.search_knowledge_base("warranty")
        assert len(results) > 0
        assert any('warranty' in r.get('question', '').lower() or
                  'warranty' in r.get('answer', '').lower()
                  for r in results)


class TestConversationService:
    """Test suite for ConversationService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = ConversationService()
        self.test_session_id = "test_session_123"

    def test_add_message(self):
        """Test adding a message to conversation"""
        self.service.create_message(
            session_id=self.test_session_id,
            role="user",
            content="Hello, how are you?"
        )
        messages = self.service.get_conversation_history(self.test_session_id)
        assert len(messages) == 1
        assert messages[0]['role'] == "user"
        assert messages[0]['content'] == "Hello, how are you?"

    def test_get_conversation_history(self):
        """Test retrieving conversation history"""
        # Add multiple messages
        self.service.create_message(self.test_session_id, "user", "First message")
        self.service.create_message(self.test_session_id, "assistant", "First response")
        self.service.create_message(self.test_session_id, "user", "Second message")

        messages = self.service.get_conversation_history(self.test_session_id)
        assert len(messages) == 3
        assert messages[0]['content'] == "First message"
        assert messages[1]['content'] == "First response"
        assert messages[2]['content'] == "Second message"

    def test_get_context_for_agent(self):
        """Test getting formatted context for agents"""
        self.service.create_message(self.test_session_id, "user", "What's the price?")
        self.service.create_message(self.test_session_id, "assistant", "It's $999", agent_type="sales")

        context = self.service.get_conversation_context_for_agent(self.test_session_id)
        assert "User: What's the price?" in context
        assert "Assistant (sales): It's $999" in context

    def test_clear_session(self):
        """Test clearing a session"""
        self.service.create_message(self.test_session_id, "user", "Test message")
        assert len(self.service.get_conversation_history(self.test_session_id)) == 1

        self.service.clear_session(self.test_session_id)
        assert len(self.service.get_conversation_history(self.test_session_id)) == 0

    def test_get_last_user_message(self):
        """Test getting the last user message"""
        self.service.create_message(self.test_session_id, "user", "First question")
        self.service.create_message(self.test_session_id, "assistant", "Response")
        self.service.create_message(self.test_session_id, "user", "Second question")

        last_message = self.service.get_last_user_message(self.test_session_id)
        assert last_message == "Second question"

    def test_get_session_summary(self):
        """Test getting session summary"""
        self.service.create_message(self.test_session_id, "user", "Question 1")
        self.service.create_message(self.test_session_id, "assistant", "Answer 1", agent_type="sales")
        self.service.create_message(self.test_session_id, "user", "Question 2")
        self.service.create_message(self.test_session_id, "assistant", "Answer 2", agent_type="technical_support")

        summary = self.service.get_session_summary(self.test_session_id)
        assert summary['total_messages'] == 4
        assert summary['user_messages'] == 2
        assert summary['assistant_messages'] == 2
        assert 'sales' in summary['agents_used']
        assert 'technical_support' in summary['agents_used']


class TestSentimentService:
    """Test suite for SentimentService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = SentimentService()

    def test_analyze_positive_sentiment(self):
        """Test analyzing positive sentiment"""
        result = self.service.analyze_sentiment("I love this product! It's amazing!")
        assert result['label'] == 'positive'
        assert result['score'] > 0

    def test_analyze_negative_sentiment(self):
        """Test analyzing negative sentiment"""
        result = self.service.analyze_sentiment("This is terrible. I hate it!")
        assert result['label'] == 'negative'
        assert result['score'] < 0

    def test_analyze_neutral_sentiment(self):
        """Test analyzing neutral sentiment"""
        result = self.service.analyze_sentiment("The product has arrived.")
        assert result['label'] == 'neutral'
        assert -0.05 <= result['score'] <= 0.05

    def test_detect_urgency(self):
        """Test urgency detection"""
        urgent_text = "URGENT! My laptop is broken and I need it immediately!"
        is_urgent, score = self.service.detect_urgency(urgent_text)
        assert is_urgent
        assert score > 0.5

    def test_detect_no_urgency(self):
        """Test non-urgent message"""
        normal_text = "I would like to know about the product specifications."
        is_urgent, score = self.service.detect_urgency(normal_text)
        assert not is_urgent
        assert score < 0.5

    def test_detect_frustration(self):
        """Test frustration detection"""
        frustrated_text = "This is ridiculous! I've been waiting for weeks and nothing works!"
        is_frustrated = self.service.detect_frustration(frustrated_text)
        assert is_frustrated

    def test_no_frustration(self):
        """Test non-frustrated message"""
        calm_text = "Thank you for your help. I appreciate it."
        is_frustrated = self.service.detect_frustration(calm_text)
        assert not is_frustrated

    def test_analyze_customer_emotion(self):
        """Test comprehensive emotion analysis"""
        text = "HELP! This is urgent! I'm so frustrated!"
        emotion = self.service.analyze_customer_emotion(text)

        assert emotion['is_urgent']
        assert emotion['is_frustrated']
        assert emotion['is_negative']
        assert emotion['requires_human_escalation']

    def test_empty_text_handling(self):
        """Test handling of empty text"""
        result = self.service.analyze_sentiment("")
        assert result['label'] == 'neutral'
        assert result['score'] == 0.0


# Integration tests would go here
class TestIntegration:
    """tests for end-to-end workflows"""

    def test_data_service_initialization(self):
        """Test that data service initializes with all data"""
        service = DataService()
        assert len(service.products) > 0
        assert len(service.orders) > 0
        assert len(service.promotions) > 0
        assert len(service.knowledge_base) > 0

    def test_conversation_flow(self):
        """Test a complete conversation flow"""
        conv_service = ConversationService()
        sentiment_service = SentimentService()

        session_id = "integration_test_session"
        user_message = "I love your products!"

        # Add user message
        conv_service.create_message(session_id, "user", user_message)

        # Analyze sentiment
        sentiment = sentiment_service.analyze_sentiment(user_message)
        assert sentiment['label'] == 'positive'

        # Add assistant response
        conv_service.create_message(
            session_id,
            "assistant",
            "Thank you! We're glad you love our products!",
            agent_type="customer_service"
        )

        # Verify conversation
        history = conv_service.get_conversation_history(session_id)
        assert len(history) == 2
        assert history[0]['role'] == "user"
        assert history[1]['role'] == "assistant"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
