# eBay Browse API Integration

This module provides integration with eBay's Browse API, allowing you to search for and discover items on eBay through the MCP server.

## Features

- **Item Search**: Search for eBay items by keywords, GTIN, ePID, or charity
- **Advanced Filtering**: Filter by price, condition, location, buying options, and more
- **Refinements**: Get metadata about search results including aspects, categories, and conditions
- **Compatibility Search**: Find items compatible with specific products (cars, trucks, motorcycles)
- **Pagination**: Navigate through large result sets
- **Multi-marketplace**: Support for eBay marketplaces worldwide

## Setup

### 1. Get eBay API Credentials

1. Visit [eBay Developer Program](https://developer.ebay.com/)
2. Create an account or sign in
3. Go to "My Account" → "Application Keys"
4. Create a new application or use an existing one
5. Get your **App ID (Client ID)**
6. Generate an **OAuth token** for production use

For detailed instructions, see: https://developer.ebay.com/api-docs/static/oauth-tokens.html

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# eBay API Configuration
EBAY_APP_ID=your_ebay_oauth_token_here
EBAY_USE_SANDBOX=false  # Set to true for sandbox testing
```

**Production OAuth Token:**
For production, you'll need to generate an OAuth 2.0 token. Use one of these methods:
- eBay's OAuth token generation tools
- Implement OAuth 2.0 flow in your application
- Use eBay's SDKs for token management

**Sandbox Testing:**
For sandbox testing:
1. Set `EBAY_USE_SANDBOX=true`
2. Use sandbox credentials from eBay Developer Portal
3. Sandbox URL: `https://api.sandbox.ebay.com/buy/browse/v1`

### 3. Restart the MCP Server

After configuring your credentials, restart the MCP server:

```bash
docker-compose restart mcp-server
```

## Usage

### Tool: `search_items`

Search for eBay items with comprehensive filtering and refinement options.

#### Basic Examples

**1. Simple Keyword Search**
```python
{
    "q": "iPhone 13",
    "limit": 10
}
```

**2. Search with Price Filter**
```python
{
    "q": "laptop",
    "filter": "price:[200..1000]",
    "sort": "price",
    "limit": 20
}
```

**3. Search by Category**
```python
{
    "q": "running shoes",
    "category_ids": "15709",
    "limit": 25
}
```

**4. Search with Multiple Filters**
```python
{
    "q": "camera",
    "filter": "price:[100..500],condition:{NEW},buyingOptions:{FIXED_PRICE}",
    "sort": "newlyListed",
    "limit": 20
}
```

**5. Search by GTIN (UPC/EAN/ISBN)**
```python
{
    "gtin": "885909950805",
    "limit": 10
}
```

**6. Search with Aspect Filter**
```python
{
    "q": "shirt",
    "category_ids": "15724",
    "aspect_filter": "categoryId:15724,Color:{Red}",
    "limit": 20
}
```

**7. Get Refinements**
```python
{
    "q": "headphones",
    "fieldgroups": "ASPECT_REFINEMENTS,CONDITION_REFINEMENTS,BUYING_OPTION_REFINEMENTS",
    "limit": 20
}
```

**8. Charity Items**
```python
{
    "q": "vintage watch",
    "charity_ids": "530196605",  # American Red Cross
    "limit": 10
}
```

**9. Compatibility Search (Automotive)**
```python
{
    "q": "brakes",
    "category_ids": "33559",
    "compatibility_filter": "Year:2018;Make:BMW;Model:X5",
    "limit": 15
}
```

**10. Pagination**
```python
# First page
{
    "q": "collectible coins",
    "limit": 50,
    "offset": 0
}

# Second page
{
    "q": "collectible coins",
    "limit": 50,
    "offset": 50
}
```

#### Parameters Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search keywords (max 100 chars). Cannot use with epid/gtin. |
| `gtin` | string | Global Trade Item Number (UPC, EAN, ISBN) |
| `epid` | string | eBay Product ID from catalog |
| `category_ids` | string | Category ID(s), comma-separated |
| `charity_ids` | string | Charity ID(s), comma-separated (max 20) |
| `filter` | string | Field filters (price, condition, location, etc.) |
| `sort` | string | Sort order: price, -price, distance, newlyListed, endingSoonest |
| `limit` | integer | Items per page (1-200, default 50) |
| `offset` | integer | Items to skip (0-9999, default 0) |
| `fieldgroups` | string | Additional data to return |
| `aspect_filter` | string | Filter by item aspects |
| `compatibility_filter` | string | Filter for compatible products |
| `auto_correct` | string | Set to 'KEYWORD' for auto-correction |
| `marketplace_id` | string | Target marketplace (EBAY_US, EBAY_GB, etc.) |
| `accept_language` | string | Language preference (e.g., en-US, fr-BE) |

#### Field Groups

- **ASPECT_REFINEMENTS**: Item aspects like color, brand, size
- **BUYING_OPTION_REFINEMENTS**: Buying options (Fixed Price, Auction, etc.)
- **CATEGORY_REFINEMENTS**: Category distributions
- **CONDITION_REFINEMENTS**: Condition distributions (New, Used, etc.)
- **EXTENDED**: Additional fields (shortDescription, city)
- **MATCHING_ITEMS**: Matching items (default)
- **FULL**: All refinements and items

#### Common Filters

```python
# Price range
"filter": "price:[10..50]"

# Condition
"filter": "condition:{NEW}"

# Buying options
"filter": "buyingOptions:{FIXED_PRICE|AUCTION}"

# Sellers
"filter": "sellers:{seller1|seller2}"

# Location (item, delivery)
"filter": "itemLocationCountry:US"

# Combined filters
"filter": "price:[100..500],condition:{NEW},buyingOptions:{FIXED_PRICE}"
```

#### Response Structure

```json
{
    "href": "https://api.ebay.com/buy/browse/v1/item_summary/search?...",
    "total": 1234,
    "next": "https://api.ebay.com/buy/browse/v1/item_summary/search?...",
    "limit": 50,
    "offset": 0,
    "itemSummaries": [
        {
            "itemId": "v1|123456789012|0",
            "title": "Apple iPhone 13 128GB - Blue",
            "price": {
                "value": "699.99",
                "currency": "USD"
            },
            "itemWebUrl": "https://www.ebay.com/itm/123456789012",
            "itemAffiliateWebUrl": "https://www.ebay.com/itm/123456789012?...",
            "image": {
                "imageUrl": "https://i.ebayimg.com/..."
            },
            "condition": "New",
            "buyingOptions": ["FIXED_PRICE"],
            "seller": {
                "username": "bestdeals",
                "feedbackPercentage": "99.8",
                "feedbackScore": 12345
            },
            "shippingOptions": [
                {
                    "shippingCostType": "FIXED",
                    "shippingCost": {
                        "value": "0.00",
                        "currency": "USD"
                    }
                }
            ]
        }
    ],
    "refinement": {
        "aspectDistributions": [...],
        "categoryDistributions": [...],
        "conditionDistributions": [...],
        "buyingOptionDistributions": [...]
    }
}
```

## Supported Marketplaces

| Marketplace ID | Country |
|---------------|---------|
| EBAY_US | United States |
| EBAY_GB | United Kingdom |
| EBAY_DE | Germany |
| EBAY_FR | France |
| EBAY_IT | Italy |
| EBAY_ES | Spain |
| EBAY_CA | Canada |
| EBAY_AU | Australia |
| EBAY_AT | Austria |
| EBAY_BE | Belgium |
| EBAY_CH | Switzerland |
| EBAY_IE | Ireland |
| EBAY_NL | Netherlands |
| EBAY_PL | Poland |

## Best Practices

### 1. Use Specific Searches
- Be specific with keywords to get better results
- Use category_ids to narrow down results
- Combine filters for precise results

### 2. Pagination
- Use limit and offset for pagination
- Maximum 10,000 items can be retrieved per search
- offset must be multiple of limit

### 3. Performance
- Request only needed fieldgroups
- Use appropriate limit values (50 is default)
- Cache results when possible

### 4. eBay Partner Network
- Use `itemAffiliateWebUrl` for commission tracking
- Required for EPN participants

### 5. Error Handling
- Handle 404 (not found)
- Handle 400 (bad request, invalid parameters)
- Handle 403 (forbidden, authentication issues)
- Handle 429 (rate limiting)

## Limitations

- Maximum 10,000 items per search
- Only FIXED_PRICE listings returned by default
- Some features only available in specific marketplaces
- Rate limits apply based on your eBay API plan

## Troubleshooting

### Error: "eBay API key not configured"
- Ensure `EBAY_APP_ID` is set in your `.env` file
- Restart the MCP server after configuration

### Error: "Invalid token"
- Regenerate your OAuth token
- Ensure token has not expired
- Check if using correct environment (production vs. sandbox)

### Error: "Rate limit exceeded"
- Reduce request frequency
- Upgrade your eBay API plan
- Implement caching

### No Results Returned
- Check keyword spelling
- Try broader search terms
- Remove some filters
- Check category ID is valid
- Verify marketplace supports the search

## Additional Resources

- [eBay Browse API Documentation](https://developer.ebay.com/api-docs/buy/browse/overview.html)
- [eBay Developer Program](https://developer.ebay.com/)
- [API Field Filters](https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html)
- [OAuth Token Guide](https://developer.ebay.com/api-docs/static/oauth-tokens.html)
- [Taxonomy API](https://developer.ebay.com/api-docs/commerce/taxonomy/overview.html)

## Support

For issues or questions:
1. Check eBay API documentation
2. Review error messages in logs
3. Verify API credentials
4. Test in sandbox environment first

