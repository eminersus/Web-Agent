"""
Basic Tools API - Time, calculations, and text analysis
"""

from fastmcp import FastMCP
from typing import Annotated, List, Dict, Any


class ToolsAPI:
    """Basic utility tools for the Web Agent"""

    def __init__(self, mcp: FastMCP):
        """
        Initialize ToolsAPI and register tools with the MCP instance.

        Args:
            mcp: FastMCP instance to register tools with
        """
        self.mcp = mcp
        self._register_tools()

    def _register_tools(self):
        """Register all tools with the MCP instance."""
        self.mcp.tool()(self.display_product_cards)

    def display_product_cards(
        self,
        products: Annotated[
            List[Dict[str, Any]],
            """List of products to display as cards. Each product should have:
            - title: Product title (required)
            - price: Price as string with currency symbol (e.g., "$299.99")
            - image: Image URL (required)
            - url: Link to product page (required)
            - itemId: Unique product identifier (optional)
            - condition: Item condition (e.g., "New", "Used") (optional)
            - seller: Seller name or info (optional)
            - location: Location string (optional)
            - shipping: Shipping info (optional)
            """,
        ],
    ) -> dict:
        """
        Display product results as visual cards in the UI.

        This tool signals the frontend to render products as visual cards instead of text.
        Use this tool after searching for products to present them in a user-friendly format.

        The backend intercepts this call and sends a special event to the frontend
        with structured product data for card rendering.

        Args:
            products: List of product dictionaries with title, price, image, and url

        Returns:
            Confirmation that products will be displayed as cards

        Example:
            After searching eBay for laptops, call this to display top 5:
            >>> display_product_cards([
            ...     {
            ...         "title": "Dell XPS 13 Laptop",
            ...         "price": "$899.99",
            ...         "image": "https://...",
            ...         "url": "https://ebay.com/itm/...",
            ...         "itemId": "123456789",
            ...         "condition": "New",
            ...         "seller": "authorized_dealer",
            ...         "location": "New York, US",
            ...         "shipping": "Free shipping"
            ...     },
            ...     # ... more products
            ... ])
        """
        # This tool is intercepted by the backend chat service
        # It never actually executes on the MCP server
        # The backend sends a special SSE event to the frontend instead

        return {
            "success": True,
            "message": f"Displaying {len(products)} product(s) as cards",
            "count": len(products),
            "note": "This tool is intercepted by the backend for UI rendering",
        }
