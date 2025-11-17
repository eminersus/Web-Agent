# eBay Browse API - Quick Reference

## Setup (5 Minutes)

1. **Get OAuth Token**: https://developer.ebay.com/
2. **Add to .env**:
   ```bash
   EBAY_APP_ID=your_oauth_token_here
   EBAY_USE_SANDBOX=false
   ```
3. **Restart**: `docker-compose restart mcp-server`

## Common Search Patterns

### Basic Search
```python
{"q": "iPhone 13", "limit": 10}
```

### Price Filter
```python
# IMPORTANT: Must include priceCurrency with price filter!
{"q": "laptop", "filter": "price:[200..1000],priceCurrency:USD", "sort": "price"}
```

### Condition Filter
```python
{"q": "camera", "filter": "condition:{NEW}"}
```

### Price + Condition Filter
```python
{"q": "camera", "filter": "price:[100..500],priceCurrency:USD,condition:{NEW}"}
```

### Multiple Filters
```python
{
    "q": "shoes",
    "filter": "price:[50..200],condition:{NEW|LIKE_NEW}",
    "sort": "newlyListed"
}
```

### Category Search
```python
{"q": "shirt", "category_ids": "15724", "limit": 20}
```

### Aspect Filter
```python
{
    "q": "shirt",
    "category_ids": "15724",
    "aspect_filter": "categoryId:15724,Color:{Red},Size:{M}"
}
```

### Get Refinements
```python
{
    "q": "headphones",
    "fieldgroups": "ASPECT_REFINEMENTS,CONDITION_REFINEMENTS"
}
```

### Pagination
```python
# Page 1
{"q": "coins", "limit": 50, "offset": 0}

# Page 2
{"q": "coins", "limit": 50, "offset": 50}
```

## Quick Filter Reference

| Filter | Example | Description |
|--------|---------|-------------|
| Price | `price:[10..50],priceCurrency:USD` | Price range (⚠️ **currency required!**) |
| Condition | `condition:{NEW}` | Item condition |
| Buying | `buyingOptions:{FIXED_PRICE}` | Fixed price only |
| Buying | `buyingOptions:{AUCTION}` | Auctions only |
| Seller | `sellers:{user1\|user2}` | Specific sellers |
| Location | `itemLocationCountry:US` | Item location |
| Multiple | `price:[10..50],priceCurrency:USD,condition:{NEW}` | Combine filters |

## Sort Options

- `price` - Lowest price first
- `-price` - Highest price first
- `distance` - Nearest first (requires location)
- `newlyListed` - Newest listings first
- `endingSoonest` - Ending soonest first

## Field Groups

- `MATCHING_ITEMS` - Just the items (default)
- `ASPECT_REFINEMENTS` - Get color, brand, etc. options
- `CONDITION_REFINEMENTS` - Get condition distributions
- `CATEGORY_REFINEMENTS` - Get category distributions
- `BUYING_OPTION_REFINEMENTS` - Get buying option distributions
- `EXTENDED` - Add description & city
- `FULL` - Everything

## Common Use Cases

### Find Cheapest Item
```python
{"q": "monitor", "sort": "price", "limit": 1}
```

### New Items Under $100
```python
{"q": "gadget", "filter": "price:[0..100],condition:{NEW}"}
```

### Auctions Ending Soon
```python
{"filter": "buyingOptions:{AUCTION}", "sort": "endingSoonest"}
```

### Items from Top Sellers
```python
{"q": "watch", "filter": "sellers:{seller1|seller2}"}
```

### Charity Items
```python
{"q": "jewelry", "charity_ids": "530196605"}
```

## Marketplaces

- `EBAY_US` - United States (default)
- `EBAY_GB` - United Kingdom
- `EBAY_DE` - Germany
- `EBAY_FR` - France
- `EBAY_CA` - Canada
- `EBAY_AU` - Australia
- See README.md for full list

## Response Fields

```json
{
    "total": 1234,
    "limit": 50,
    "offset": 0,
    "itemSummaries": [
        {
            "itemId": "v1|123|0",
            "title": "Item Title",
            "price": {"value": "99.99", "currency": "USD"},
            "itemWebUrl": "https://...",
            "itemAffiliateWebUrl": "https://...",  // Use for EPN
            "condition": "New",
            "buyingOptions": ["FIXED_PRICE"]
        }
    ]
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key not configured" | Set `EBAY_APP_ID` in .env |
| "Invalid token" | Regenerate OAuth token |
| No results | Try broader keywords |
| Rate limit | Reduce request frequency |

## Pro Tips

1. **Be Specific**: Use category_ids to narrow results
2. **Use Refinements**: Get aspects first, then filter
3. **Combine Filters**: More filters = better results
4. **Sort Wisely**: Choose appropriate sort for your use case
5. **Paginate**: Use offset for browsing large results
6. **Cache Results**: Save API calls by caching
7. **Use Affiliate URLs**: `itemAffiliateWebUrl` for commissions

## Limits

- Max 10,000 items per search
- Max 200 items per page
- Offset must be multiple of limit
- Default returns FIXED_PRICE only

## Learn More

- Full Documentation: `README.md`
- Usage Examples: `examples.py`
- eBay API Docs: https://developer.ebay.com/api-docs/buy/browse/overview.html

