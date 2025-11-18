"""
eBay Browse API - Item search and discovery tools
"""

from fastmcp import FastMCP
from typing import Annotated, Optional, Dict, Any
import logging
import os
import requests
import base64
from datetime import datetime, timedelta

from schemas.ebay_schemas import (
    ItemSummarySearchParams,
    ItemSummarySearchResponse,
    EbayErrorResponse
)

logger = logging.getLogger(__name__)


class EbayBrowseAPI:
    """
    eBay Browse API tools for searching and discovering items on eBay.
    
    This API provides access to eBay's Browse API, allowing users to:
    - Search for items by keywords, GTIN, ePID, or charity
    - Filter results by various criteria (price, condition, location, etc.)
    - Get refinements and metadata about search results
    - Access item details and compatibility information
    """
    
    # eBay API configuration
    EBAY_API_BASE_URL = "https://api.ebay.com/buy/browse/v1"
    EBAY_SANDBOX_URL = "https://api.sandbox.ebay.com/buy/browse/v1"
    
    def __init__(self, mcp: FastMCP):
        """
        Initialize EbayBrowseAPI and register tools with the MCP instance.
        
        Args:
            mcp: FastMCP instance to register tools with
        """
        self.mcp = mcp
        self.api_key = os.getenv("EBAY_APP_ID", "")
        self.client_id = os.getenv("EBAY_CLIENT_ID", "")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET", "")
        self.use_sandbox = os.getenv("EBAY_USE_SANDBOX", "false").lower() == "true"
        self.base_url = self.EBAY_SANDBOX_URL if self.use_sandbox else self.EBAY_API_BASE_URL
        self.token_expiry = None
        self._register_tools()
    
    def _register_tools(self):
        """Register all eBay Browse API tools with the MCP instance."""
        self.mcp.tool()(self.search_items)
    
    def _refresh_token(self) -> bool:
        """
        Refresh the OAuth access token using client credentials.
        
        Returns:
            True if token was refreshed successfully, False otherwise
        """
        if not self.client_id or not self.client_secret:
            logger.warning("Cannot refresh token: EBAY_CLIENT_ID or EBAY_CLIENT_SECRET not set")
            return False
        
        # Determine token endpoint
        if self.use_sandbox:
            token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        else:
            token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        
        # Encode credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        b64_credentials = base64.b64encode(credentials.encode()).decode()
        
        # Prepare request
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {b64_credentials}"
        }
        
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        try:
            logger.info("Refreshing eBay OAuth token...")
            response = requests.post(token_url, headers=headers, data=data, timeout=30.0)
            
            if response.status_code == 200:
                token_data = response.json()
                self.api_key = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 7200)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)  # Refresh 5 min early
                logger.info(f"Token refreshed successfully. Expires in {expires_in} seconds")
                return True
            else:
                logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error refreshing token: {e}", exc_info=True)
            return False
    
    def _ensure_valid_token(self) -> bool:
        """
        Ensure we have a valid access token, refreshing if necessary.
        
        Returns:
            True if we have a valid token, False otherwise
        """
        # If no token at all, try to get one
        if not self.api_key:
            logger.info("No access token found, attempting to obtain one...")
            return self._refresh_token()
        
        # If token is expired or about to expire, refresh it
        if self.token_expiry and datetime.now() >= self.token_expiry:
            logger.info("Access token expired, refreshing...")
            return self._refresh_token()
        
        return True
    
    def _get_headers(self, marketplace_id: str = "EBAY_US", accept_language: Optional[str] = None) -> Dict[str, str]:
        """
        Get the HTTP headers required for eBay API requests.
        
        Args:
            marketplace_id: eBay marketplace identifier (default: EBAY_US)
            accept_language: Natural language preference (e.g., 'en-US', 'fr-BE')
        
        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
            "Content-Type": "application/json"
        }
        
        if accept_language:
            headers["Accept-Language"] = accept_language
        
        return headers
    
    def search_items(
        self,
        q: Annotated[Optional[str], "Search keywords (e.g., 'iPhone 13'). Use spaces for AND, comma-separated in parentheses for OR"] = None,
        gtin: Annotated[Optional[str], "Global Trade Item Number (GTIN) - UPC, EAN, or ISBN"] = None,
        epid: Annotated[Optional[str], "eBay Product ID (ePID) from eBay product catalog"] = None,
        category_ids: Annotated[Optional[str], "Category ID(s) to limit results (comma-separated)"] = None,
        charity_ids: Annotated[Optional[str], "Charity ID(s) to filter items (comma-separated, max 20)"] = None,
        filter: Annotated[Optional[str], "Field filters (e.g., 'price:[10..50]', 'sellers:{seller1|seller2}')"] = None,
        sort: Annotated[Optional[str], "Sort order: 'price', '-price', 'distance', 'newlyListed', 'endingSoonest'"] = None,
        limit: Annotated[int, "Number of items per page (1-200)"] = 50,
        offset: Annotated[int, "Number of items to skip (0-9999)"] = 0,
        fieldgroups: Annotated[Optional[str], "Data to return: ASPECT_REFINEMENTS, BUYING_OPTION_REFINEMENTS, CATEGORY_REFINEMENTS, CONDITION_REFINEMENTS, EXTENDED, MATCHING_ITEMS, FULL"] = None,
        aspect_filter: Annotated[Optional[str], "Filter by item aspects (e.g., 'categoryId:15724,Color:{Red}')"] = None,
        compatibility_filter: Annotated[Optional[str], "Filter for compatible products (e.g., 'Year:2018;Make:BMW')"] = None,
        auto_correct: Annotated[Optional[str], "Enable auto-correction: 'KEYWORD'"] = None,
        marketplace_id: Annotated[str, "eBay marketplace (e.g., EBAY_US, EBAY_GB, EBAY_DE)"] = "EBAY_US",
        accept_language: Annotated[Optional[str], "Language preference (e.g., 'en-US', 'fr-BE')"] = None
    ) -> Dict[str, Any]:
        """
        Search for eBay items by various criteria and retrieve item summaries.
        
        This method searches for eBay items using keywords, category, eBay product ID (ePID),
        GTIN, charity ID, or combinations thereof. Only listings with FIXED_PRICE (Buy It Now)
        are returned by default unless the buyingOptions filter is used.
        
        Key Features:
        - Search by keyword, category, product ID, or GTIN
        - Filter by price, condition, location, buying options, and more
        - Get refinements (metadata) like item aspects, categories, conditions
        - Filter by item aspects and compatibility
        - Pagination and sorting controls
        - Returns up to 10,000 items maximum
        
        Important Notes:
        - Do not combine keywords (q) with epid or gtin
        - epid and gtin may be combined together
        - For eBay Partner Network commissions, use itemAffiliateWebUrl from results
        - Auto-correction only supported in: US, AT, AU, CA, CH, DE, ES, FR, GB, IE, IT
        - Compatibility filter only supports cars, trucks, and motorcycles
        
        Args:
            q: Search keywords. Spaces = AND, comma-separated in parentheses = OR.
               Max 100 characters. Cannot be used with epid or gtin.
            gtin: Global Trade Item Number (UPC, EAN, ISBN). Can be combined with epid.
            epid: eBay Product ID from catalog. Can be combined with gtin.
            category_ids: Limit to category ID(s). Currently supports one ID per request.
            charity_ids: Filter by charity IDs (US: EIN, UK: CRN). Max 20 IDs.
            filter: Field filters like 'price:[10..50]' or 'sellers:{seller1|seller2}'.
            sort: Sort by 'price', '-price', 'distance', 'newlyListed', or 'endingSoonest'.
            limit: Items per page (1-200, default 50).
            offset: Items to skip for pagination (0-9999, default 0). Must be multiple of limit.
            fieldgroups: Additional data to return (comma-separated):
                - ASPECT_REFINEMENTS: aspect distributions
                - BUYING_OPTION_REFINEMENTS: buying option distributions
                - CATEGORY_REFINEMENTS: category distributions
                - CONDITION_REFINEMENTS: condition distributions
                - EXTENDED: adds shortDescription and itemLocation.city
                - MATCHING_ITEMS: matching items (default)
                - FULL: all refinements and matching items
            aspect_filter: Filter by aspects like 'categoryId:15724,Color:{Red}'.
            compatibility_filter: Product attributes like 'Year:2018;Make:BMW'.
            auto_correct: Set to 'KEYWORD' to enable keyword auto-correction.
            marketplace_id: Target marketplace (EBAY_US, EBAY_GB, etc.).
            accept_language: Language preference (e.g., 'en-US', 'fr-BE').
        
        Returns:
            Dictionary containing:
            - itemSummaries: List of matching items with details
            - total: Total number of matching items
            - limit/offset: Pagination info
            - href/next/prev: URLs for current/next/previous pages
            - refinement: Metadata and distributions (if requested)
            - warnings: Any warnings from the API
        
        Examples:
            Search for iPhones:
            >>> search_items(q="iPhone 13", limit=10)
            
            Search with price filter:
            >>> search_items(q="laptop", filter="price:[200..1000]", sort="price")
            
            Search by category with aspects:
            >>> search_items(
            ...     q="shirt",
            ...     category_ids="15724",
            ...     aspect_filter="categoryId:15724,Color:{Red}",
            ...     limit=20
            ... )
            
            Search with refinements:
            >>> search_items(
            ...     q="camera",
            ...     fieldgroups="ASPECT_REFINEMENTS,CONDITION_REFINEMENTS",
            ...     limit=25
            ... )
        """
        # Ensure limit and offset are integers (in case they come as strings from tool calls)
        limit = int(limit) if not isinstance(limit, int) else limit
        offset = int(offset) if not isinstance(offset, int) else offset
        
        # Ensure we have a valid token
        if not self._ensure_valid_token():
            logger.warning("Unable to obtain valid eBay access token")
            
            # Provide helpful error message based on configuration
            if self.client_id and self.client_secret:
                error_msg = (
                    "Failed to obtain eBay access token using client credentials. "
                    "Please verify EBAY_CLIENT_ID and EBAY_CLIENT_SECRET are correct."
                )
            else:
                error_msg = (
                    "eBay API token not configured. Please either:\n"
                    "1. Set EBAY_APP_ID with a valid OAuth token, OR\n"
                    "2. Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET for automatic token refresh"
                )
            
            return {
                "error": "eBay API token not configured or invalid",
                "message": error_msg,
                "integration_needed": True,
                "documentation": "https://developer.ebay.com/api-docs/buy/browse/overview.html",
                "help": "Run: cd mcp-server/api/ebay && python get_ebay_token.py"
            }
        
        # Build query parameters
        params = {}
        if q:
            params["q"] = q
        if gtin:
            params["gtin"] = gtin
        if epid:
            params["epid"] = epid
        if category_ids:
            params["category_ids"] = category_ids
        if charity_ids:
            params["charity_ids"] = charity_ids
        if filter:
            params["filter"] = filter
        if sort:
            params["sort"] = sort
        if fieldgroups:
            params["fieldgroups"] = fieldgroups
        if aspect_filter:
            params["aspect_filter"] = aspect_filter
        if compatibility_filter:
            params["compatibility_filter"] = compatibility_filter
        if auto_correct:
            params["auto_correct"] = auto_correct
        
        # Always include limit and offset
        params["limit"] = str(limit)
        params["offset"] = str(offset)
        
        # Log the search request
        logger.info(f"eBay item search: {params}")
        
        try:
            # Make API request
            url = f"{self.base_url}/item_summary/search"
            headers = self._get_headers(marketplace_id, accept_language)
            
            response = requests.get(url, params=params, headers=headers, timeout=30.0)
            
            # Handle response
            if response.status_code == 200:
                data = response.json()
                logger.info(f"eBay search successful: {data.get('total', 0)} items found")
                
                # Return raw JSON data for LLM to process
                return data
            else:
                # Parse error response
                error_data = response.json() if response.text else {}
                logger.error(f"eBay API error: {response.status_code} - {error_data}")
                
                # Handle 401 specifically (invalid/expired token)
                if response.status_code == 401:
                    # Try to refresh token and retry once
                    logger.info("Received 401 error, attempting token refresh...")
                    if self._refresh_token():
                        logger.info("Token refreshed, retrying request...")
                        # Retry the request with new token
                        headers = self._get_headers(marketplace_id, accept_language)
                        retry_response = requests.get(url, params=params, headers=headers, timeout=30.0)
                        if retry_response.status_code == 200:
                            data = retry_response.json()
                            logger.info(f"Retry successful: {data.get('total', 0)} items found")
                            return data
                    
                    # If refresh failed or retry failed, return helpful error
                    return {
                        "error": "Invalid or expired eBay access token",
                        "status_code": 401,
                        "details": error_data,
                        "message": "Your eBay access token is invalid or has expired.",
                        "solution": (
                            "OAuth tokens expire after ~2 hours. To fix this:\n"
                            "1. Run: cd mcp-server/api/ebay && python get_ebay_token.py\n"
                            "2. OR set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET for automatic refresh\n"
                            "3. Update EBAY_APP_ID in your .env file with the new token\n"
                            "4. Restart the MCP server"
                        )
                    }
                
                return {
                    "error": f"eBay API returned status {response.status_code}",
                    "status_code": response.status_code,
                    "details": error_data,
                    "message": "Failed to search eBay items"
                }
        
        except requests.Timeout:
            logger.error("eBay API request timed out")
            return {
                "error": "Request timeout",
                "message": "eBay API request timed out after 30 seconds"
            }
        
        except Exception as e:
            logger.error(f"Error calling eBay API: {e}", exc_info=True)
            return {
                "error": "API request failed",
                "message": str(e),
                "type": type(e).__name__
            }
    
    def _format_for_display(self, data: Dict[str, Any], requested_limit: int) -> str:
        """
        Format eBay API response for beautiful display in LibreChat UI.
        Creates markdown-formatted cards with images and product info.
        
        Args:
            data: Raw eBay API response
            requested_limit: Number of items requested (for display purposes)
        
        Returns:
            Markdown formatted string for direct display
        """
        items = data.get('itemSummaries', [])
        total = data.get('total', 0)
        
        # Create markdown formatted display
        display_parts = []
        
        # Header with search summary
        display_parts.append(f"# 🛍️ eBay Search Results\n\n")
        display_parts.append(f"**Found {total:,} items** (showing {len(items)})\n\n")
        display_parts.append("---\n\n")
        
        # Format each item as a card
        for idx, item in enumerate(items[:requested_limit], 1):
            card = self._format_item_card(item, idx)
            display_parts.append(card)
        
        # Add pagination info if there are more results
        if total > len(items):
            remaining = total - len(items)
            display_parts.append(f"\n---\n\n")
            display_parts.append(f"💡 **{remaining:,} more items available** - Increase limit or use offset for pagination\n\n")
        
        # Return the markdown string directly
        return "".join(display_parts)
    
    def _format_item_card(self, item: Dict[str, Any], index: int) -> str:
        """
        Format a single eBay item as a markdown card.
        
        Args:
            item: Item data from eBay API
            index: Item number in the list
        
        Returns:
            Markdown formatted card
        """
        # Extract item details
        title = item.get('title', 'No title')
        price_obj = item.get('price', {})
        price = price_obj.get('value', 'N/A')
        currency = price_obj.get('currency', '')
        price_display = f"${price} {currency}" if price != 'N/A' else 'Price not available'
        
        condition = item.get('condition', 'N/A')
        image = item.get('image', {})
        image_url = image.get('imageUrl', '')
        item_url = item.get('itemWebUrl', '#')
        
        # Seller info
        seller = item.get('seller', {})
        seller_name = seller.get('username', 'Unknown')
        seller_feedback = seller.get('feedbackPercentage', 'N/A')
        
        # Location
        location = item.get('itemLocation', {})
        city = location.get('city', '')
        country = location.get('country', '')
        location_str = f"{city}, {country}" if city else country
        
        # Shipping
        shipping_opts = item.get('shippingOptions', [])
        shipping_info = "Shipping info available" if shipping_opts else "See listing for shipping"
        if shipping_opts:
            first_ship = shipping_opts[0]
            ship_cost = first_ship.get('shippingCost', {})
            ship_value = ship_cost.get('value', '')
            if ship_value == '0.00' or ship_value == '0.0':
                shipping_info = "✅ Free shipping"
        
        # Build the card
        card_parts = []
        
        # Card header with index
        card_parts.append(f"\n## {index}. {title}\n\n")
        
        # Image (if available)
        if image_url:
            card_parts.append(f"![Product Image]({image_url})\n\n")
        
        # Price and condition row
        card_parts.append(f"### 💰 **{price_display}** | 📦 {condition}\n\n")
        
        # Details
        card_parts.append(f"- **Seller:** {seller_name} ({seller_feedback}% positive)\n")
        if location_str:
            card_parts.append(f"- **Location:** {location_str}\n")
        card_parts.append(f"- **Shipping:** {shipping_info}\n")
        
        # View listing button
        card_parts.append(f"\n[🔗 View on eBay]({item_url})\n\n")
        
        # Divider
        card_parts.append("---\n\n")
        
        return "".join(card_parts)

