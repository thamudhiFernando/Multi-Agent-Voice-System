from typing import Optional

from crewai.tools import tool
from pydantic import BaseModel, Field

from app.core.logs import get_logger
from app.knowledge_base.vector_store import get_vector_store
from app.services.data_service import get_data_service

logger = get_logger()


# Tool Input Schemas

class ProductSearchInput(BaseModel):
    """Input schema for product search tool"""
    query: str = Field(..., description="Search query for products")
    category: Optional[str] = Field(None, description="Filter by category")
    max_results: int = Field(5, description="Maximum number of results to return")


class OrderLookupInput(BaseModel):
    """Input schema for order lookup tool"""
    order_id: str = Field(..., description="Order ID to look up")


class PromotionSearchInput(BaseModel):
    """Input schema for promotion search tool"""
    query: Optional[str] = Field(None, description="Search query for promotions")
    category: Optional[str] = Field(None, description="Filter by category")


class KnowledgeBaseSearchInput(BaseModel):
    """Input schema for knowledge base search tool"""
    query: str = Field(..., description="Search query for knowledge base")
    kb_type: str = Field(..., description="Knowledge base type: technical_support, return_policy, shipping_policy, store_info, loyalty_program")


# Tool Functions

def product_search_func(query: str, category: Optional[str] = None, max_results: int = 5) -> str:
    """Execute product search"""
    try:
        logger.info(f"Product search: query='{query}', category='{category}'")

        vector_store = get_vector_store()
        # data_service = get_data_service()

        # Use vector store for semantic search
        products = vector_store.search_products(query, n_results=max_results)

        # If category specified, filter results
        if category and products:
            products = [p for p in products if p.get('category', '').lower() == category.lower()]

        if not products:
            return f"No products found matching '{query}'."

        # Format results
        results = []
        for product in products[:max_results]:
            result = (
                f"**{product['name']}** (ID: {product['id']})\n"
                f"- Brand: {product['brand']}\n"
                f"- Category: {product['category']}\n"
                f"- Price: ${product['price']}\n"
                f"- Stock: {product['stock_status']} ({product['stock_quantity']} units)\n"
                f"- Description: {product['description']}\n"
            )
            results.append(result)

        return "\n\n".join(results)

    except Exception as e:
        logger.error(f"Error in product search: {e}")
        return f"Error searching products: {str(e)}"


def order_lookup_func(order_id: str) -> str:
    """Execute order lookup"""
    try:
        logger.info(f"Order lookup: order_id='{order_id}'")

        data_service = get_data_service()
        order = data_service.get_order_by_id(order_id)

        if not order:
            return f"Order {order_id} not found. Please verify the order ID."

        # Format order details
        items_text = "\n".join([
            f"  - {item['product_name']} (Qty: {item['quantity']}) - ${item['price']}"
            for item in order.get('items', [])
        ])

        tracking_info = ""
        if order.get('tracking_number'):
            tracking_info = (
                f"- Carrier: {order.get('carrier')}\n"
                f"- Tracking Number: {order['tracking_number']}\n"
            )

        result = (
            f"**Order {order['order_id']}**\n"
            f"- Status: {order['status']}\n"
            f"- Order Date: {order['order_date']}\n"
            f"- Customer: {order['customer_name']}\n"
            f"- Email: {order['customer_email']}\n"
            f"- Total Amount: ${order['total_amount']}\n"
            f"- Shipping Address: {order['shipping_address']}\n"
            f"{tracking_info}"
            f"- Shipping Status: {order['shipping_status']}\n"
            f"- Estimated Delivery: {order.get('estimated_delivery', 'N/A')}\n\n"
            f"**Items:**\n{items_text}"
        )

        return result

    except Exception as e:
        logger.error(f"Error in order lookup: {e}")
        return f"Error looking up order: {str(e)}"


def promotion_search_func(query: Optional[str] = None, category: Optional[str] = None) -> str:
    """Execute promotion search"""
    try:
        logger.info(f"Promotion search: query='{query}', category='{category}'")

        data_service = get_data_service()

        # Get active promotions
        if category:
            promotions = data_service.get_promotions_by_category(category)
        else:
            promotions = data_service.get_all_promotions(active_only=True)

        # Filter by query if provided
        if query and promotions:
            query_lower = query.lower()
            promotions = [
                p for p in promotions
                if query_lower in p.get('name', '').lower()
                or query_lower in p.get('description', '').lower()
            ]

        if not promotions:
            return "No active promotions found at this time."

        # Format results
        results = []
        for promo in promotions:
            requirements = f"\n- Requirements: {promo['requirements']}" if promo.get('requirements') else ""
            result = (
                f"**{promo['name']}** (Code: {promo['code']})\n"
                f"- {promo['description']}\n"
                f"- Discount: {promo['discount_value']}{'%' if promo['discount_type'] == 'percentage' else '$'}\n"
                f"- Applicable to: {', '.join(promo['applicable_categories'])}\n"
                f"- Valid: {promo['start_date']} to {promo['end_date']}"
                f"{requirements}"
            )
            results.append(result)

        return "\n\n".join(results)

    except Exception as e:
        logger.error(f"Error in promotion search: {e}")
        return f"Error searching promotions: {str(e)}"


def knowledge_base_search_func(query: str, kb_type: str = "default") -> str:
    """Execute knowledge base search"""
    try:
        # Map 'default' to a real collection
        if kb_type == "default":
            kb_type = "technical_support"

        logger.info(f"KB search: query='{query}', kb_type='{kb_type}'")

        vector_store = get_vector_store()

        # Check collection exists
        if kb_type not in vector_store.collections:
            logger.error(f"Collection '{kb_type}' does not exist in vector store")
            return f"No relevant information found: collection '{kb_type}' does not exist."

        # Search using RAG
        articles = vector_store.search_knowledge_base(query, kb_type, n_results=3)

        if not articles:
            return f"No relevant information found in {kb_type} knowledge base."

        # Format results
        results = []
        for article in articles:
            result = (
                f"**Q: {article.get('question', 'N/A')}**\n"
                f"A: {article.get('answer', 'N/A')}"
            )
            results.append(result)

        return "\n\n".join(results)

    except Exception as e:
        logger.error(f"Error in KB search: {e}")
        return f"Error searching knowledge base: {str(e)}"


# Create Tool instances for agents

@tool("Product Search")
def product_search_tool(query: str) -> str:
    """
    Search for products by name, category, brand, or description.
    Returns detailed product information including price, specs, and availability.
    """
    return product_search_func(query)


@tool("Order Lookup")
def order_lookup_tool(order_id: str) -> str:
    """
    Look up order details, shipping status, and tracking information using order ID.
    """
    return order_lookup_func(order_id)


@tool("Promotion Search")
def promotion_search_tool(query: str) -> str:
    """
    Search for active promotions, discounts, deals, and loyalty program information.
    """
    return promotion_search_func(query)


@tool("Knowledge Base Search")
def knowledge_base_search_tool(query: str) -> str:
    """
    Search knowledge base for technical support, policies, troubleshooting guides, and FAQs.
    """
    return knowledge_base_search_func(query)
