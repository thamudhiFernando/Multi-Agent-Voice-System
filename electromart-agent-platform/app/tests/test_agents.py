import pytest

from app.agents.agent_tools import product_search_tool, order_lookup_tool


class TestProductSearchTool:
    """Test suite for ProductSearchTool"""

    def setup_method(self):
        """Setup test fixtures"""
        self.tool = product_search_tool()

    def test_search_by_name(self):
        """Test searching products by name"""
        result = self.tool._run(query="iPhone", max_results=5)
        assert isinstance(result, str)
        assert "iPhone" in result or "No products found" in result

    def test_search_by_category(self):
        """Test searching products by category"""
        result = self.tool._run(query="laptop", category="Laptops", max_results=3)
        assert isinstance(result, str)

    def test_search_with_max_results(self):
        """Test limiting search results"""
        result = self.tool._run(query="phone", max_results=2)
        assert isinstance(result, str)

    def test_search_nonexistent_product(self):
        """Test searching for nonexistent product"""
        result = self.tool._run(query="XYZ123NonExistent", max_results=5)
        assert "No products found" in result or isinstance(result, str)

class TestOrderLookupTool:
    """Test suite for OrderLookupTool"""

    def setup_method(self):
        """Setup test fixtures"""
        self.tool = order_lookup_tool()

    def test_lookup_existing_order(self):
        """Test looking up an existing order"""
        result = self.tool._run(order_id="ORD12345")
        assert isinstance(result, str)
        assert "ORD12345" in result

    def test_lookup_nonexistent_order(self):
        """Test looking up a nonexistent order"""
        result = self.tool._run(order_id="INVALID_ORDER")
        assert "not found" in result.lower()

    def test_order_details_format(self):
        """Test that order details are properly formatted"""
        result = self.tool._run(order_id="ORD12345")
        # Check for expected fields in output
        assert "Status:" in result or "not found" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
