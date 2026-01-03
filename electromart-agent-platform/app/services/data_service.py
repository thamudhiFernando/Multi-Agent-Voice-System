import json
from typing import Optional, List, Any, Dict

from app.core.config import settings
from app.core.logs import get_logger

logger = get_logger()


class DataService:
    """
    Service class for managing mock data operations.
    Loads data from JSON files and provides query methods.
    """

    def __init__(self):
        """Initialize data service and load all data"""
        self.products: List[Dict[str, Any]] = []
        self.orders: List[Dict[str, Any]] = []
        self.promotions: List[Dict[str, Any]] = []
        self.knowledge_base: Dict[str, Any] = {}
        self._load_all_data()

    def _load_all_data(self):
        """Load all mock data from JSON files"""
        try:
            self._load_products()
            self._load_orders()
            self._load_promotions()
            self._load_knowledge_base()
            logger.info("All mock data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading mock data: {e}")
            raise

    def _load_products(self):
        """Load products data from JSON file"""
        try:
            with open(settings.PRODUCTS_DATA_PATH, 'r') as f:
                self.products = json.load(f)
            logger.info(f"Loaded {len(self.products)} products")
        except FileNotFoundError:
            logger.error(f"Products file not found: {settings.PRODUCTS_DATA_PATH}")
            self.products = []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing products JSON: {e}")
            self.products = []

    def _load_orders(self):
        """Load orders data from JSON file"""
        try:
            with open(settings.ORDERS_DATA_PATH, 'r') as f:
                self.orders = json.load(f)
            logger.info(f"Loaded {len(self.orders)} orders")
        except FileNotFoundError:
            logger.error(f"Orders file not found: {settings.ORDERS_DATA_PATH}")
            self.orders = []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing orders JSON: {e}")
            self.orders = []

    def _load_promotions(self):
        """Load promotions data from JSON file"""
        try:
            with open(settings.PROMOTIONS_DATA_PATH, 'r') as f:
                self.promotions = json.load(f)
            logger.info(f"Loaded {len(self.promotions)} promotions")
        except FileNotFoundError:
            logger.error(f"Promotions file not found: {settings.PROMOTIONS_DATA_PATH}")
            self.promotions = []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing promotions JSON: {e}")
            self.promotions = []

    def _load_knowledge_base(self):
        """Load knowledge base data from JSON file"""
        try:
            with open(settings.KNOWLEDGE_BASE_PATH, 'r') as f:
                self.knowledge_base = json.load(f)
            logger.info("Loaded knowledge base successfully")
        except FileNotFoundError:
            logger.error(f"Knowledge base file not found: {settings.KNOWLEDGE_BASE_PATH}")
            self.knowledge_base = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing knowledge base JSON: {e}")
            self.knowledge_base = {}

    # Product Methods

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products"""
        return self.products

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product by ID

        Args:
            product_id: Product ID to search for

        Returns:
            Product dict if found, None otherwise
        """
        for product in self.products:
            if product.get('id') == product_id:
                return product
        return None

    def search_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search products with multiple filters

        Args:
            query: Search query for name/description
            category: Filter by category
            brand: Filter by brand
            min_price: Minimum price filter
            max_price: Maximum price filter
            in_stock_only: Filter only in-stock products

        Returns:
            List of matching products
        """
        results = self.products

        # Filter by query
        if query:
            query_lower = query.lower()
            results = [
                p for p in results
                if query_lower in p.get('name', '').lower()
                or query_lower in p.get('description', '').lower()
                or query_lower in p.get('brand', '').lower()
            ]

        # Filter by category
        if category:
            results = [p for p in results if p.get('category', '').lower() == category.lower()]

        # Filter by brand
        if brand:
            results = [p for p in results if p.get('brand', '').lower() == brand.lower()]

        # Filter by price range
        if min_price is not None:
            results = [p for p in results if p.get('price', 0) >= min_price]
        if max_price is not None:
            results = [p for p in results if p.get('price', float('inf')) <= max_price]

        # Filter by stock
        if in_stock_only:
            results = [p for p in results if p.get('stock_status') == 'in_stock']

        return results

    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all products in a specific category"""
        return [p for p in self.products if p.get('category', '').lower() == category.lower()]

    # Order Methods

    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        return self.orders

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order by order ID

        Args:
            order_id: Order ID to search for

        Returns:
            Order dict if found, None otherwise
        """
        for order in self.orders:
            if order.get('order_id') == order_id:
                return order
        return None

    def get_orders_by_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Get all orders for a specific customer email

        Args:
            email: Customer email address

        Returns:
            List of orders for that customer
        """
        return [o for o in self.orders if o.get('customer_email', '').lower() == email.lower()]

    def get_orders_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all orders with a specific status"""
        return [o for o in self.orders if o.get('status', '').lower() == status.lower()]

    # Promotion Methods

    def get_all_promotions(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all promotions

        Args:
            active_only: If True, only return active promotions

        Returns:
            List of promotions
        """
        if active_only:
            return [p for p in self.promotions if p.get('status') == 'active']
        return self.promotions

    def get_promotion_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get promotion by promo code

        Args:
            code: Promotion code

        Returns:
            Promotion dict if found, None otherwise
        """
        for promo in self.promotions:
            if promo.get('code', '').upper() == code.upper():
                return promo
        return None

    def get_promotions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all active promotions applicable to a category"""
        return [
            p for p in self.promotions
            if p.get('status') == 'active'
            and (category in p.get('applicable_categories', []) or 'All' in p.get('applicable_categories', []))
        ]

    # Knowledge Base Methods

    def get_technical_support_kb(self) -> List[Dict[str, Any]]:
        """Get all technical support knowledge base articles"""
        return self.knowledge_base.get('technical_support', [])

    def get_return_policy_kb(self) -> List[Dict[str, Any]]:
        """Get all return policy knowledge base articles"""
        return self.knowledge_base.get('return_policy', [])

    def get_shipping_policy_kb(self) -> List[Dict[str, Any]]:
        """Get all shipping policy knowledge base articles"""
        return self.knowledge_base.get('shipping_policy', [])

    def get_store_info_kb(self) -> List[Dict[str, Any]]:
        """Get store information"""
        return self.knowledge_base.get('store_info', [])

    def get_loyalty_program_kb(self) -> List[Dict[str, Any]]:
        """Get loyalty program information"""
        return self.knowledge_base.get('loyalty_program', [])

    def search_knowledge_base(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search knowledge base articles

        Args:
            query: Search query
            category: Optional category filter (technical_support, return_policy, etc.)

        Returns:
            List of matching KB articles
        """
        query_lower = query.lower()
        results = []

        # Determine which categories to search
        categories_to_search = [category] if category else self.knowledge_base.keys()

        for cat in categories_to_search:
            articles = self.knowledge_base.get(cat, [])
            for article in articles:
                # Search in question, answer, and tags
                if (query_lower in article.get('question', '').lower()
                    or query_lower in article.get('answer', '').lower()
                    or any(query_lower in tag.lower() for tag in article.get('tags', []))):
                    results.append({**article, 'kb_category': cat})

        return results


# Create a global instance
data_service = DataService()


def get_data_service() -> DataService:
    """
    Dependency function to get data service instance.

    Returns:
        DataService: Global data service instance
    """
    return data_service
