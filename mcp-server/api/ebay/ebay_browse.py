"""
eBay Browse API - Item search and discovery tools
"""

from fastmcp import FastMCP
from typing import Annotated, Optional, Dict, Any
import logging
import os
import requests
import base64
import random
from datetime import datetime, timedelta

from schemas.ebay_schemas import (
    ItemSummarySearchParams,
    ItemSummarySearchResponse,
    EbayErrorResponse
)

logger = logging.getLogger(__name__)


class EbayBrowseAPI:
    """
    eBay Browse API and Taxonomy API tools for searching and discovering items on eBay.
    
    This API provides access to eBay's Browse API and Taxonomy API, allowing users to:
    - Search for items by keywords, GTIN, ePID, or charity
    - Filter results by various criteria (price, condition, location, etc.)
    - Get refinements and metadata about search results
    - Access item details and compatibility information
    - Get category suggestions based on keywords
    - Get item aspects (item specifics) for categories
    """
    
    # eBay API configuration
    EBAY_API_BASE_URL = "https://api.ebay.com/buy/browse/v1"
    EBAY_SANDBOX_URL = "https://api.sandbox.ebay.com/buy/browse/v1"
    EBAY_TAXONOMY_API_BASE_URL = "https://api.ebay.com/commerce/taxonomy/v1"
    EBAY_TAXONOMY_SANDBOX_URL = "https://api.sandbox.ebay.com/commerce/taxonomy/v1"
    
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
        self.taxonomy_base_url = self.EBAY_TAXONOMY_SANDBOX_URL if self.use_sandbox else self.EBAY_TAXONOMY_API_BASE_URL
        self.token_expiry = None
        self._register_tools()
    
    def _register_tools(self):
        """Register all eBay Browse API tools with the MCP instance."""
        self.mcp.tool()(self.search_items)
        # Taxonomy API tools
        self.mcp.tool()(self.get_category_suggestions)
        self.mcp.tool()(self.get_item_aspects_for_category)
    
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
        aspect_filter: Annotated[Optional[str], "Filter by item aspects. CRITICAL: Category ID must be specified in BOTH category_ids parameter AND in aspect_filter as 'categoryId:XXXXX'. Format: 'categoryId:XXXXX,AspectName:{Value1|Value2}'. Use localizedAspectName and localizedValue from get_item_aspects_for_category. Multiple values use pipe: {Value1|Value2}. To escape pipe in values, use backslash: {Bed\\|Stü|Nike}. Example: 'categoryId:15724,Color:{Red|Blue},Size:{M|L}'. Both category_ids and aspect_filter must use the SAME category ID. To discover available aspects, use get_item_aspects_for_category or set fieldgroups='ASPECT_REFINEMENTS' in search_items."] = None,
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
            aspect_filter: Filter by item aspects. ⚠️ CRITICAL REQUIREMENT: The category ID must be specified TWICE:
                          1. In the 'category_ids' parameter (e.g., category_ids="15724")
                          2. In the 'aspect_filter' as 'categoryId:XXXXX' (e.g., aspect_filter="categoryId:15724,...")
                          These two values MUST be the same category ID.
                          
                          Format: 'categoryId:XXXXX,AspectName:{Value1|Value2},AnotherAspect:{Value}'
                          
                          How to get aspect names and values:
                          - Use get_item_aspects_for_category(category_id) to get all aspects for a category
                          - OR use fieldgroups="ASPECT_REFINEMENTS" in search_items to get aspect distributions
                          
                          Use 'localizedAspectName' from aspects as the aspect name (e.g., "Color", "Brand", "Size").
                          Use 'localizedValue' from aspectValues as the filter values (e.g., "Red", "Apple", "M").
                          
                          Multiple values use pipe separator: {Value1|Value2} (e.g., {Red|Blue|Green}).
                          To escape pipe symbol in values, use backslash: {Bed\\|Stü|Nike} (for brand "Bed|Stü").
                          
                          Examples:
                          - Single aspect: 'categoryId:15724,Color:{Red}'
                          - Multiple values: 'categoryId:15724,Color:{Red|Blue},Size:{M|L}'
                          - With escaped pipe: 'categoryId:3034,Brand:{Bed\\|Stü|Nike}'
                          
                          Complete example:
                          >>> search_items(
                          ...     q="shirt",
                          ...     category_ids="15724",  # Category ID here
                          ...     aspect_filter="categoryId:15724,Color:{Red}",  # Same category ID here
                          ...     limit=20
                          ... )
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
            
            Search by category with aspects (⚠️ Category ID must be in BOTH category_ids AND aspect_filter):
            Step 1: Get aspects for category
            >>> aspects = get_item_aspects_for_category(category_id="15724")
            # Returns: {"aspects": [{"localizedAspectName": "Color", "aspectValues": [{"localizedValue": "Red"}, ...]}, ...]}
            
            Step 2: Use aspects in search (NOTE: category_ids="15724" AND aspect_filter starts with "categoryId:15724")
            >>> search_items(
            ...     q="shirt",
            ...     category_ids="15724",  # Category ID specified here
            ...     aspect_filter="categoryId:15724,Color:{Red|Blue},Size:{M|L}",  # Same category ID here
            ...     limit=20
            ... )
            
            Alternative: Discover aspects using ASPECT_REFINEMENTS
            >>> search_items(
            ...     q="shirt",
            ...     category_ids="15724",
            ...     fieldgroups="ASPECT_REFINEMENTS",
            ...     limit=20
            ... )
            # Returns refinement.aspectDistributions with available aspects and values
            
            Note: 
            - Use localizedAspectName from aspects as the aspect name
            - Use localizedValue from aspectValues as the filter values
            - Category ID in category_ids MUST match categoryId in aspect_filter
            - To escape pipe in values (e.g., brand "Bed|Stü"), use: {Bed\\|Stü|Nike}
            
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
            # Validate that category ID in aspect_filter matches category_ids if both are provided
            if category_ids:
                # Extract categoryId from aspect_filter (format: "categoryId:XXXXX,...")
                import re
                aspect_cat_match = re.search(r'categoryId:(\d+)', aspect_filter)
                if aspect_cat_match:
                    aspect_category_id = aspect_cat_match.group(1)
                    # Check if category_ids contains this ID (could be comma-separated)
                    category_ids_list = [cat.strip() for cat in category_ids.split(',')]
                    if aspect_category_id not in category_ids_list:
                        logger.warning(
                            f"Category ID mismatch: category_ids={category_ids} but aspect_filter has categoryId:{aspect_category_id}. "
                            "These should match according to eBay API requirements."
                        )
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
    
    def _get_default_category_tree_id(self, marketplace_id: str) -> Optional[str]:
        """
        Get the default category tree ID for a marketplace.
        This is a helper method used by other Taxonomy API methods.
        
        Args:
            marketplace_id: eBay marketplace identifier (e.g., 'EBAY_US', 'EBAY_GB')
        
        Returns:
            Category tree ID as string, or None if failed
        """
        try:
            url = f"{self.taxonomy_base_url}/get_default_category_tree_id"
            headers = self._get_headers(marketplace_id)
            params = {
                "marketplace_id": marketplace_id
            }
            
            logger.info(f"Fetching default category tree ID for marketplace: {marketplace_id}")
            response = requests.get(url, params=params, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                category_tree_id = data.get("categoryTreeId")
                
                if not category_tree_id:
                    logger.error(f"No categoryTreeId in response: {data}")
                    return None
                
                # Ensure it's a string and not the marketplace_id
                category_tree_id = str(category_tree_id)
                if category_tree_id == marketplace_id:
                    logger.error(f"Category tree ID matches marketplace_id (likely error): {category_tree_id}")
                    return None
                
                logger.info(f"Retrieved category tree ID '{category_tree_id}' for marketplace {marketplace_id}")
                return category_tree_id
            else:
                error_data = response.json() if response.text else {}
                logger.error(f"Failed to get category tree ID: {response.status_code} - {error_data}")
                return None
        except Exception as e:
            logger.error(f"Error getting category tree ID: {e}", exc_info=True)
            return None
    
    def get_category_suggestions(
        self,
        q: Annotated[str, "Search query/keywords to find suggested categories (e.g., 'iPhone 13', 'laptop', 'running shoes')"],
        marketplace_id: Annotated[str, "eBay marketplace identifier (e.g., 'EBAY_US', 'EBAY_GB', 'EBAY_DE')"] = "EBAY_US",
        accept_language: Annotated[Optional[str], "Language preference for category names (e.g., 'en-US', 'fr-BE')"] = None
    ) -> Dict[str, Any]:
        """
        Get suggested eBay categories based on a keyword query.
        
        This method helps identify the most appropriate categories for listing items
        or searching by providing category suggestions based on keywords. It's particularly
        useful when you're not sure which category to use for a product.
        
        **How it works:**
        1. Automatically retrieves the default category tree ID for the marketplace
        2. Uses that category tree ID to get category suggestions based on your keywords
        3. Returns a list of suggested categories with their full hierarchy paths
        
        **Use Cases:**
        - Finding the right category when listing a new item
        - Discovering category structure for a product type
        - Understanding which categories are most relevant for specific keywords
        - Getting category IDs for use in search filters
        
        **Response includes:**
        - Suggested categories with IDs and names
        - Category hierarchy level (depth in the tree)
        - Full ancestor path (parent categories up to root)
        - Category tree version information
        
        Args:
            q: Search query/keywords to find matching categories. Examples:
               - "iPhone 13" - suggests electronics/cell phone categories
               - "laptop" - suggests computer/electronics categories
               - "running shoes" - suggests clothing/shoes categories
            marketplace_id: eBay marketplace identifier (default: EBAY_US).
                          Different marketplaces may have different category structures.
            accept_language: Language preference for category names (e.g., 'en-US', 'fr-BE').
                            If not specified, uses marketplace default.
        
        Returns:
            Dictionary containing:
            - categorySuggestions: List of suggested categories, each with:
                - category: Category info (categoryId, categoryName)
                - categoryTreeNodeLevel: Depth level in the category tree
                - categoryTreeNodeAncestors: Array of parent categories showing full path
            - categoryTreeId: The category tree ID used
            - categoryTreeVersion: Version of the category tree
        
        Examples:
            Get category suggestions for "iPhone":
            >>> get_category_suggestions(q="iPhone 13")
            
            Get suggestions for "laptop" in UK marketplace:
            >>> get_category_suggestions(q="laptop", marketplace_id="EBAY_GB")
            
            Get suggestions for "running shoes" in French:
            >>> get_category_suggestions(q="running shoes", marketplace_id="EBAY_FR", accept_language="fr-FR")
        
        **Example Response:**
        ```json
        {
            "categorySuggestions": [
                {
                    "category": {
                        "categoryId": "9355",
                        "categoryName": "Cell Phones & Smartphones"
                    },
                    "categoryTreeNodeLevel": 2,
                    "categoryTreeNodeAncestors": [
                        {
                            "categoryId": "15032",
                            "categoryName": "Cell Phones & Accessories",
                            "categoryTreeNodeLevel": 1
                        }
                    ]
                }
            ],
            "categoryTreeId": "0",
            "categoryTreeVersion": "117"
        }
        ```
        
        **Error Handling:**
        - Returns error if keyword 'q' is missing
        - Returns error if marketplace_id is invalid
        - Returns error if category tree ID cannot be retrieved
        """
        # Ensure we have a valid token
        if not self._ensure_valid_token():
            logger.warning("Unable to obtain valid eBay access token")
            return {
                "error": "eBay API token not configured or invalid",
                "message": "Please configure EBAY_APP_ID or EBAY_CLIENT_ID/EBAY_CLIENT_SECRET",
                "integration_needed": True
            }
        
        try:
            # Step 1: Get the default category tree ID for the marketplace
            category_tree_id = self._get_default_category_tree_id(marketplace_id)
            if not category_tree_id:
                return {
                    "error": "Failed to retrieve category tree ID",
                    "message": f"Could not get default category tree for marketplace {marketplace_id}. Please verify your eBay API credentials and marketplace ID.",
                    "status_code": 500,
                    "help": "The category tree ID is required to get category suggestions. This may indicate an issue with the eBay Taxonomy API or your credentials."
                }
            
            # Validate category_tree_id is not the marketplace_id
            if category_tree_id == marketplace_id:
                logger.error(f"Category tree ID is same as marketplace_id - this is incorrect")
                return {
                    "error": "Invalid category tree ID",
                    "message": f"Category tree ID retrieval returned marketplace_id instead of actual tree ID",
                    "status_code": 500
                }
            
            # Step 2: Get category suggestions using the category tree ID
            url = f"{self.taxonomy_base_url}/category_tree/{category_tree_id}/get_category_suggestions"
            headers = self._get_headers(marketplace_id, accept_language)
            params = {
                "q": q
            }
            
            logger.info(f"Getting category suggestions for query: '{q}' using category tree ID: {category_tree_id} (marketplace: {marketplace_id})")
            response = requests.get(url, params=params, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                suggestions_count = len(data.get("categorySuggestions", []))
                logger.info(f"Category suggestions retrieved successfully: {suggestions_count} suggestions found")
                return data
            else:
                error_data = response.json() if response.text else {}
                logger.error(f"eBay Taxonomy API error: {response.status_code} - {error_data}")
                
                if response.status_code == 401:
                    # Try to refresh token and retry once
                    logger.info("Received 401 error, attempting token refresh...")
                    if self._refresh_token():
                        logger.info("Token refreshed, retrying request...")
                        # Get category tree ID again after refresh
                        category_tree_id = self._get_default_category_tree_id(marketplace_id)
                        if category_tree_id:
                            url = f"{self.taxonomy_base_url}/category_tree/{category_tree_id}/get_category_suggestions"
                            headers = self._get_headers(marketplace_id, accept_language)
                            retry_response = requests.get(url, params=params, headers=headers, timeout=30.0)
                            if retry_response.status_code == 200:
                                data = retry_response.json()
                                logger.info("Retry successful")
                                return data
                
                # Handle specific error codes
                error_code = error_data.get("errors", [{}])[0].get("errorId", "") if error_data.get("errors") else ""
                if error_code == "62007":
                    return {
                        "error": "Missing keyword parameter",
                        "status_code": response.status_code,
                        "details": "The 'q' parameter is required",
                        "error_code": error_code
                    }
                elif error_code == "62004":
                    return {
                        "error": "Category tree not found",
                        "status_code": response.status_code,
                        "details": f"Category tree ID {category_tree_id} not found",
                        "error_code": error_code
                    }
                
                return {
                    "error": f"eBay Taxonomy API returned status {response.status_code}",
                    "status_code": response.status_code,
                    "details": error_data,
                    "error_code": error_code
                }
        
        except requests.Timeout:
            logger.error("eBay Taxonomy API request timed out")
            return {
                "error": "Request timeout",
                "message": "eBay Taxonomy API request timed out after 30 seconds"
            }
        
        except Exception as e:
            logger.error(f"Error calling eBay Taxonomy API: {e}", exc_info=True)
            return {
                "error": "API request failed",
                "message": str(e),
                "type": type(e).__name__
            }
    
    def get_item_aspects_for_category(
        self,
        category_id: Annotated[str, "eBay category ID to get aspects for"],
        marketplace_id: Annotated[str, "eBay marketplace identifier (e.g., 'EBAY_US', 'EBAY_GB')"] = "EBAY_US",
        accept_language: Annotated[Optional[str], "Language preference (e.g., 'en-US', 'fr-BE')"] = None
    ) -> Dict[str, Any]:
        """
        Get item aspects (item specifics) for a specific category.
        
        Item aspects are the required or recommended attributes for listing items
        in a category (e.g., Brand, Color, Size for clothing). This method helps
        understand what information is needed when listing items in a category.
        
        ⚠️ IMPORTANT: HOW TO USE ASPECTS IN SEARCH ⚠️
        
        After getting aspects from this tool, use them in the 'aspect_filter' parameter
        of the 'search_items' tool to filter search results by those aspects.
        
        Format for aspect_filter in search_items:
        'categoryId:XXXXX,AspectName:{Value1|Value2},AnotherAspect:{Value}'
        
        ⚠️ CRITICAL REQUIREMENT: Category ID must be specified TWICE:
        - In search_items 'category_ids' parameter (e.g., category_ids="15724")
        - In search_items 'aspect_filter' as 'categoryId:XXXXX' (e.g., aspect_filter="categoryId:15724,...")
        These two values MUST be the same category ID!
        
        Steps:
        1. Call this tool to get aspects for a category (note the categoryId in response)
        2. Extract the 'localizedAspectName' from the aspects list (e.g., "Color", "Brand", "Size")
        3. Extract valid values from 'aspectValues' array (use 'localizedValue', e.g., "Red", "Apple", "M")
        4. Use them in search_items with BOTH category_ids AND aspect_filter:
           - category_ids="15724" (use the categoryId from this response)
           - aspect_filter="categoryId:15724,Color:{Red|Blue},Size:{M|L}" (same categoryId here)
        
        Example Workflow:
        Step 1: Get aspects
        >>> aspects_result = get_item_aspects_for_category(category_id="15724")
        # Returns aspects like: Brand, Color, Size, etc.
        
        Step 2: Use in search
        >>> search_items(
        ...     q="shirt",
        ...     category_ids="15724",
        ...     aspect_filter="categoryId:15724,Color:{Red|Blue},Size:{M|L}",
        ...     limit=20
        ... )
        
        Key Points:
        - Use 'localizedAspectName' as the aspect name in aspect_filter
        - Use 'localizedValue' from aspectValues for the values
        - Multiple values use pipe separator: {Value1|Value2}
        - Always include categoryId in aspect_filter
        - Values must match exactly (case-sensitive)
        
        Args:
            category_id: eBay category ID to retrieve aspects for
            marketplace_id: eBay marketplace identifier (default: EBAY_US)
            accept_language: Language preference for aspect names (e.g., 'en-US', 'fr-BE')
        
        Returns:
            Dictionary containing:
            - categoryId: The category ID requested (USE THIS in aspect_filter)
            - categoryTreeId: Category tree identifier
            - categoryTreeVersion: Version of the category tree
            - aspects: List of aspects with:
                - localizedAspectName: The aspect name to use in aspect_filter (e.g., "Brand", "Color", "Size")
                - aspectValues: Array of valid values, each with:
                    - localizedValue: The exact value to use in aspect_filter (e.g., "Red", "Apple", "M")
                - aspectConstraint: Constraints (REQUIRED, RECOMMENDED, etc.)
                - relevanceIndicator: Relevance indicator
        
        Examples:
            Get aspects for a clothing category:
            >>> get_item_aspects_for_category(category_id="15724")
            # Returns aspects including: Brand, Color, Size, Material, etc.
            # Use these in search_items aspect_filter like:
            # aspect_filter="categoryId:15724,Color:{Red},Size:{M}"
            
            Get aspects for electronics category in UK:
            >>> get_item_aspects_for_category(category_id="58058", marketplace_id="EBAY_GB")
            # Returns aspects including: Brand, Model, Screen Size, etc.
            # Use in search: aspect_filter="categoryId:58058,Brand:{Apple|Samsung},Screen Size:{13 inch|15 inch}"
        """
        # Ensure we have a valid token
        if not self._ensure_valid_token():
            logger.warning("Unable to obtain valid eBay access token")
            return {
                "error": "eBay API token not configured or invalid",
                "message": "Please configure EBAY_APP_ID or EBAY_CLIENT_ID/EBAY_CLIENT_SECRET",
                "integration_needed": True
            }
        
        try:
            # Step 1: Get the default category tree ID for the marketplace
            category_tree_id = self._get_default_category_tree_id(marketplace_id)
            if not category_tree_id:
                return {
                    "error": "Failed to retrieve category tree ID",
                    "message": f"Could not get default category tree for marketplace {marketplace_id}",
                    "status_code": 500
                }
            
            # Step 2: Build URL using category tree ID (not marketplace_id)
            url = f"{self.taxonomy_base_url}/category_tree/{category_tree_id}/get_item_aspects_for_category"
            headers = self._get_headers(marketplace_id, accept_language)
            params = {
                "category_id": category_id
            }
            
            logger.info(f"Getting item aspects for category: {category_id} (using category tree ID: {category_tree_id})")
            response = requests.get(url, params=params, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Item aspects retrieved successfully for category {category_id}")
                
                # Add usage instructions and example values to help the model understand how to use these aspects
                if isinstance(data, dict) and "aspects" in data:
                    cat_id = data.get('categoryId', category_id)
                    
                    # Build aspect filters with example values for the LLM
                    aspect_filters = []
                    for aspect in data.get('aspects', []):
                        aspect_name = aspect.get('localizedAspectName', '')
                        if not aspect_name:
                            continue
                        
                        # Get all available values
                        aspect_values = aspect.get('aspectValues', [])
                        all_values = [val.get('localizedValue', '') for val in aspect_values if val.get('localizedValue')]
                        
                        # Pick 5 random example values (or all if less than 5)
                        if all_values:
                            num_examples = min(5, len(all_values))
                            example_values = random.sample(all_values, num_examples)
                            
                            # Format example values for aspect_filter
                            example_values_str = '|'.join(example_values)
                            
                            aspect_filters.append({
                                "aspectName": aspect_name,
                                "exampleValues": example_values,
                                "exampleUsage": f"{aspect_name}:{{{example_values_str}}}",
                                "totalAvailableValues": len(all_values)
                            })
                    
                    usage_note = {
                        "usage_instructions": {
                            "critical_requirement": (
                                "⚠️ CRITICAL: Category ID must be specified TWICE in search_items:\n"
                                f"1. In 'category_ids' parameter: category_ids=\"{cat_id}\"\n"
                                f"2. In 'aspect_filter' as 'categoryId:XXXXX': aspect_filter=\"categoryId:{cat_id},...\"\n"
                                "These two values MUST be the same!"
                            ),
                            "how_to_use_in_search": (
                                "To filter search results using these aspects, use BOTH parameters in 'search_items':\n"
                                f"1. category_ids=\"{cat_id}\" (required)\n"
                                f"2. aspect_filter=\"categoryId:{cat_id},AspectName:{{Value1|Value2}}\" (required)\n\n"
                                "Steps:\n"
                                "1. Use the aspect filters below - each has example values you can use\n"
                                "2. Combine multiple aspects in aspect_filter separated by commas\n"
                                f"3. Always start with categoryId:{cat_id} in aspect_filter\n\n"
                                "Complete Example:\n"
                                f"search_items(\n"
                                f"    q=\"shirt\",\n"
                                f"    category_ids=\"{cat_id}\",  # Category ID here\n"
                                f"    aspect_filter=\"categoryId:{cat_id},Color:{{Red|Blue}},Size:{{M|L}}\",  # Same category ID here\n"
                                f"    limit=20\n"
                                f")\n\n"
                                "Pipe Escaping:\n"
                                "If a value contains pipe symbol (e.g., brand 'Bed|Stü'), escape it with backslash:\n"
                                f"aspect_filter=\"categoryId:{cat_id},Brand:{{Bed\\\\|Stü|Nike}}\""
                            ),
                            "format": f"categoryId:{cat_id},AspectName:{{Value1|Value2}},AnotherAspect:{{Value}}",
                            "required_category_id": cat_id,
                            "alternative_discovery": (
                                "You can also discover aspects by using fieldgroups=\"ASPECT_REFINEMENTS\" in search_items:\n"
                                "search_items(q=\"shirt\", category_ids=\"15724\", fieldgroups=\"ASPECT_REFINEMENTS\")\n"
                                "This returns refinement.aspectDistributions with available aspects and their value distributions."
                            )
                        },
                        "aspectFilters": aspect_filters
                    }
                    # Add usage note to the response
                    data["_usage_guide"] = usage_note

                return data
            else:
                error_data = response.json() if response.text else {}
                logger.error(f"eBay Taxonomy API error: {response.status_code} - {error_data}")

                if response.status_code == 401:
                    # Try to refresh token and retry once
                    logger.info("Received 401 error, attempting token refresh...")
                    if self._refresh_token():
                        logger.info("Token refreshed, retrying request...")
                        # Get category tree ID again after refresh
                        category_tree_id = self._get_default_category_tree_id(marketplace_id)
                        if category_tree_id:
                            url = f"{self.taxonomy_base_url}/category_tree/{category_tree_id}/get_item_aspects_for_category"
                            headers = self._get_headers(marketplace_id, accept_language)
                            retry_response = requests.get(url, params=params, headers=headers, timeout=30.0)
                            if retry_response.status_code == 200:
                                data = retry_response.json()
                                logger.info("Retry successful")
                                return data
                
                # Handle specific error codes
                error_code = error_data.get("errors", [{}])[0].get("errorId", "") if error_data.get("errors") else ""
                if error_code == "62004":
                    return {
                        "error": "Category tree not found",
                        "status_code": response.status_code,
                        "details": f"Category tree ID {category_tree_id} not found for marketplace {marketplace_id}",
                        "error_code": error_code,
                        "help": "This may indicate the marketplace is not supported or the category tree ID is invalid"
                    }

                return {
                    "error": f"eBay Taxonomy API returned status {response.status_code}",
                    "status_code": response.status_code,
                    "details": error_data,
                    "error_code": error_code
                }

        except requests.Timeout:
            logger.error("eBay Taxonomy API request timed out")
            return {
                "error": "Request timeout",
                "message": "eBay Taxonomy API request timed out after 30 seconds"
            }

        except Exception as e:
            logger.error(f"Error calling eBay Taxonomy API: {e}", exc_info=True)
            return {
                "error": "API request failed",
                "message": str(e),
                "type": type(e).__name__
            }
