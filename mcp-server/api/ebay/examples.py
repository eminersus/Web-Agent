"""
Example usage of the eBay Browse API

This file demonstrates various ways to use the eBay item search functionality.
These examples show the parameters you would pass to the search_items tool.
"""

# Example 1: Simple keyword search
simple_search = {
    "q": "iPhone 13",
    "limit": 10
}

# Example 2: Search with price filtering
# IMPORTANT: Must include priceCurrency with price filter!
price_filtered_search = {
    "q": "laptop",
    "filter": "price:[200..1000],priceCurrency:USD",
    "sort": "price",
    "limit": 20
}

# Example 3: Search by category with aspects
category_aspect_search = {
    "q": "shirt",
    "category_ids": "15724",  # Women's Clothing category
    "aspect_filter": "categoryId:15724,Color:{Red},Size:{M}",
    "limit": 20
}

# Example 4: Search with multiple filters
multi_filter_search = {
    "q": "digital camera",
    "filter": "price:[100..500],priceCurrency:USD,condition:{NEW},buyingOptions:{FIXED_PRICE}",
    "sort": "newlyListed",
    "limit": 25
}

# Example 5: Search with refinements
refinement_search = {
    "q": "wireless headphones",
    "fieldgroups": "ASPECT_REFINEMENTS,CONDITION_REFINEMENTS,BUYING_OPTION_REFINEMENTS",
    "limit": 20
}

# Example 6: Search by GTIN (UPC/EAN)
gtin_search = {
    "gtin": "885909950805",  # Example GTIN for iPhone
    "limit": 10
}

# Example 7: Search by eBay Product ID (ePID)
epid_search = {
    "epid": "15032",  # Example ePID
    "limit": 10
}

# Example 8: Charity items search
charity_search = {
    "q": "vintage watch",
    "charity_ids": "530196605",  # American Red Cross
    "limit": 10
}

# Example 9: Automotive compatibility search
compatibility_search = {
    "q": "brake pads",
    "category_ids": "33559",  # Brakes category
    "compatibility_filter": "Year:2018;Make:BMW;Model:X5",
    "limit": 15
}

# Example 10: Extended information search
extended_search = {
    "q": "vintage vinyl records",
    "fieldgroups": "EXTENDED,ASPECT_REFINEMENTS",
    "limit": 20,
    "sort": "price"
}

# Example 11: Location-based search with price
location_search = {
    "q": "furniture",
    "filter": "price:[50..500],priceCurrency:USD,itemLocationCountry:US,deliveryCountry:US",
    "sort": "price",
    "limit": 20
}

# Example 12: Seller-specific search
seller_search = {
    "q": "collectibles",
    "filter": "sellers:{topseller123|greatseller456}",
    "limit": 20
}

# Example 13: Auction listings
auction_search = {
    "q": "rare coins",
    "filter": "buyingOptions:{AUCTION}",
    "sort": "endingSoonest",
    "limit": 20
}

# Example 14: New condition items only
new_items_search = {
    "q": "smartphone",
    "filter": "condition:{NEW}",
    "sort": "price",
    "limit": 30
}

# Example 15: Pagination example (page 2)
paginated_search = {
    "q": "vintage books",
    "limit": 50,
    "offset": 50,  # Skip first 50 items
    "sort": "newlyListed"
}

# Example 16: Multi-marketplace search (UK)
uk_marketplace_search = {
    "q": "tea set",
    "marketplace_id": "EBAY_GB",
    "accept_language": "en-GB",
    "limit": 20
}

# Example 17: OR keyword search
or_search = {
    "q": "(iPhone, Samsung)",  # Items with either iPhone OR Samsung
    "limit": 20
}

# Example 18: AND keyword search
and_search = {
    "q": "laptop gaming",  # Items with both laptop AND gaming
    "limit": 20
}

# Example 19: Complex filter combination
complex_search = {
    "q": "DSLR camera",
    "category_ids": "625",  # Digital Cameras
    "filter": "price:[300..1500],priceCurrency:USD,condition:{NEW|LIKE_NEW},deliveryCountry:US",
    "fieldgroups": "EXTENDED,ASPECT_REFINEMENTS,CONDITION_REFINEMENTS",
    "sort": "newlyListed",
    "limit": 25
}

# Example 20: Auto-correct enabled search
autocorrect_search = {
    "q": "iPohne 13",  # Intentional typo
    "auto_correct": "KEYWORD",
    "limit": 10
}

# All examples as a dictionary for easy access
EXAMPLES = {
    "simple_search": simple_search,
    "price_filtered_search": price_filtered_search,
    "category_aspect_search": category_aspect_search,
    "multi_filter_search": multi_filter_search,
    "refinement_search": refinement_search,
    "gtin_search": gtin_search,
    "epid_search": epid_search,
    "charity_search": charity_search,
    "compatibility_search": compatibility_search,
    "extended_search": extended_search,
    "location_search": location_search,
    "seller_search": seller_search,
    "auction_search": auction_search,
    "new_items_search": new_items_search,
    "paginated_search": paginated_search,
    "uk_marketplace_search": uk_marketplace_search,
    "or_search": or_search,
    "and_search": and_search,
    "complex_search": complex_search,
    "autocorrect_search": autocorrect_search,
}


def print_examples():
    """Print all examples with descriptions"""
    print("eBay Browse API - Example Searches\n")
    print("=" * 80)
    
    for name, params in EXAMPLES.items():
        print(f"\n{name}:")
        print("-" * 80)
        for key, value in params.items():
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("\nTo use these examples, call the search_items tool with the parameters shown.")


if __name__ == "__main__":
    print_examples()

