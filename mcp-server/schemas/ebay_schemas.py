"""
Pydantic schemas for eBay Browse API
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ItemSummarySearchParams(BaseModel):
    """
    Query parameters for the eBay item_summary/search endpoint.
    """
    
    q: Optional[str] = Field(
        None,
        description=(
            "A string consisting of one or more keywords used to search for items on eBay. "
            "The * wildcard character is not allowed. When providing two or more keywords: "
            "- Separated by space: processed as AND request (e.g., 'iphone ipad') "
            "- Comma-separated in parentheses: processed as OR request (e.g., '(iphone, ipad)'). "
            "Maximum length: 100 characters. "
            "Note: Do not combine with epid or gtin parameters."
        ),
        max_length=100
    )
    
    gtin: Optional[str] = Field(
        None,
        description=(
            "Search by Global Trade Item Number (GTIN) of the product. "
            "Supported GTIN types are UPC, EAN, and ISBN. "
            "May be combined with epid, but not with q (keywords)."
        )
    )
    
    charity_ids: Optional[str] = Field(
        None,
        description=(
            "Filters results to return only items associated with specified charity IDs. "
            "Comma-separated list of up to 20 charity IDs. "
            "In the US: Employer Identification Number (EIN). "
            "In the UK: Charity Registration Number (CRN). "
            "Only supported by US and UK marketplaces. "
            "May be combined with category_ids and/or q keywords."
        )
    )
    
    fieldgroups: Optional[str] = Field(
        None,
        description=(
            "Comma-separated list of values controlling what is returned in the response. "
            "Valid values: "
            "- ASPECT_REFINEMENTS: adds aspectDistributions container (category specific) "
            "- BUYING_OPTION_REFINEMENTS: adds buyingOptionDistributions container "
            "- CATEGORY_REFINEMENTS: adds categoryDistributions container "
            "- CONDITION_REFINEMENTS: adds conditionDistributions containers "
            "- EXTENDED: adds shortDescription and itemLocation.city "
            "- MATCHING_ITEMS: returns items matching keyword/category (default) "
            "- FULL: returns all refinement containers and all matching items"
        )
    )
    
    compatibility_filter: Optional[str] = Field(
        None,
        description=(
            "Specifies product attributes to filter compatible items (cars, trucks, motorcycles only). "
            "Format: attribute:value pairs separated by semicolons (e.g., 'Year:2018;Make:BMW'). "
            "Requires q (keyword) and one parts-compatibility-supported category ID. "
            "Returns compatibility information and CompatibilityMatchEnum values. "
            "Note: Testing in Sandbox only supported with mock data."
        )
    )
    
    auto_correct: Optional[str] = Field(
        None,
        description=(
            "Enables auto-correction for keywords. Valid value: 'KEYWORD'. "
            "Supported marketplaces: US, AT, AU, CA, CH, DE, ES, FR, GB, IE, IT."
        )
    )
    
    category_ids: Optional[str] = Field(
        None,
        description=(
            "Limits results to specified category ID(s). Single category ID or comma-separated list. "
            "Note: Currently only one category ID per request is supported. "
            "May be combined with epid/gtin OR q keywords. "
            "If top-level (L1) category specified, must include q parameter. "
            "Category IDs vary by marketplace - use Taxonomy API or Category Changes page."
        )
    )
    
    filter: Optional[str] = Field(
        None,
        description=(
            "Array of field filters to limit/customize results. "
            "Examples: "
            "- Price range: 'price:[10..50]' "
            "- Sellers: 'sellers:{rpseller|bigSal}' "
            "- Combined: 'price:[10..50],sellers:{rpseller|bigSal}'. "
            "See Buy API Field Filters documentation for all supported filters."
        )
    )
    
    sort: Optional[str] = Field(
        None,
        description=(
            "Specifies sorting criteria for returned items. Options: "
            "- 'price': ascending order by total cost (price + shipping), lowest first "
            "- '-price': descending order, highest first "
            "- 'distance': by distance from buyer's location, closest first (requires pickup filters) "
            "- 'newlyListed': by itemOriginDate, newly listed first "
            "- 'endingSoonest': by end date/time, ending soonest first. "
            "Default: 'Best Match' if not specified."
        )
    )
    
    limit: Optional[int] = Field(
        50,
        ge=1,
        le=200,
        description=(
            "Number of items returned in a single page. "
            "If set, offset must be zero or a multiple of limit. "
            "Min: 1, Max: 200, Default: 50. "
            "Note: Method can return maximum of 10,000 items total."
        )
    )
    
    offset: Optional[int] = Field(
        0,
        ge=0,
        le=9999,
        description=(
            "Number of items to skip in the result set for pagination. "
            "Must be zero or a multiple of limit value. "
            "Examples: offset=0, limit=10 returns items 1-10; offset=10, limit=10 returns items 11-20. "
            "Min: 0, Max: 9,999, Default: 0. "
            "Note: Method can return maximum of 10,000 items total."
        )
    )
    
    aspect_filter: Optional[str] = Field(
        None,
        description=(
            "Filters by item aspects (name/value pairs) within a category. "
            "Category ID must be specified in both category_ids parameter and aspect_filter. "
            "Format: 'categoryId:ID,AspectName:{Value}' "
            "Example: 'categoryId:15724,Color:{Red}' for women's red shirts. "
            "Pipe symbol (|) used as delimiter between values. "
            "Escape pipe in values with backslash (e.g., 'Brand:{Bed\\|Stü|Nike}'). "
            "Use fieldgroups=ASPECT_REFINEMENTS to get available aspects."
        )
    )
    
    epid: Optional[str] = Field(
        None,
        description=(
            "eBay Product Identifier (ePID) from eBay product catalog. "
            "Limits results to items in the specified ePID. "
            "Use Catalog API product_summary/search to find ePIDs. "
            "May be combined with gtin, but not with q (keywords)."
        )
    )


class ItemLocation(BaseModel):
    """Location information for an item"""
    city: Optional[str] = Field(None, description="City where the item is located")
    country: Optional[str] = Field(None, description="Country where the item is located")
    postalCode: Optional[str] = Field(None, description="Postal code of the item location")


class Image(BaseModel):
    """Image information for an item"""
    imageUrl: Optional[str] = Field(None, description="URL of the item image")
    height: Optional[int] = Field(None, description="Height of the image in pixels")
    width: Optional[int] = Field(None, description="Width of the image in pixels")


class Price(BaseModel):
    """Price information for an item"""
    value: Optional[str] = Field(None, description="Price value as a string")
    currency: Optional[str] = Field(None, description="Currency code (e.g., USD, EUR)")


class Seller(BaseModel):
    """Seller information"""
    username: Optional[str] = Field(None, description="Seller's eBay username")
    feedbackPercentage: Optional[str] = Field(None, description="Seller's positive feedback percentage")
    feedbackScore: Optional[int] = Field(None, description="Seller's feedback score")


class ShippingOption(BaseModel):
    """Shipping option details"""
    shippingCostType: Optional[str] = Field(None, description="Type of shipping cost (e.g., FIXED, CALCULATED)")
    shippingCost: Optional[Price] = Field(None, description="Shipping cost")


class ItemSummary(BaseModel):
    """Summary information for a single eBay item"""
    itemId: Optional[str] = Field(None, description="Unique eBay item identifier")
    title: Optional[str] = Field(None, description="Title of the item")
    price: Optional[Price] = Field(None, description="Current price of the item")
    itemWebUrl: Optional[str] = Field(None, description="URL to view the item on eBay")
    itemAffiliateWebUrl: Optional[str] = Field(
        None, 
        description="eBay Partner Network affiliate URL (use this for commissions)"
    )
    image: Optional[Image] = Field(None, description="Primary image of the item")
    additionalImages: Optional[List[Image]] = Field(None, description="Additional item images")
    condition: Optional[str] = Field(None, description="Item condition (e.g., NEW, USED)")
    conditionId: Optional[str] = Field(None, description="Condition identifier")
    itemLocation: Optional[ItemLocation] = Field(None, description="Location where the item is located")
    categories: Optional[List[Dict[str, str]]] = Field(None, description="Categories the item belongs to")
    buyingOptions: Optional[List[str]] = Field(
        None, 
        description="Available buying options (e.g., FIXED_PRICE, AUCTION, BEST_OFFER)"
    )
    seller: Optional[Seller] = Field(None, description="Information about the seller")
    shippingOptions: Optional[List[ShippingOption]] = Field(None, description="Available shipping options")
    shortDescription: Optional[str] = Field(None, description="Short description (available with EXTENDED fieldgroup)")
    itemGroupHref: Optional[str] = Field(None, description="URL to item group if item is part of a group")
    itemGroupType: Optional[str] = Field(None, description="Type of item group")


class AspectDistribution(BaseModel):
    """Distribution of aspect values"""
    localizedAspectName: Optional[str] = Field(None, description="Localized name of the aspect")
    aspectValueDistributions: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Distribution of values for this aspect"
    )


class CategoryDistribution(BaseModel):
    """Distribution of items across categories"""
    categoryId: Optional[str] = Field(None, description="Category identifier")
    categoryName: Optional[str] = Field(None, description="Category name")
    matchCount: Optional[int] = Field(None, description="Number of matching items in this category")
    refinementHref: Optional[str] = Field(None, description="URL to refine search by this category")


class BuyingOptionDistribution(BaseModel):
    """Distribution of buying options"""
    buyingOption: Optional[str] = Field(None, description="Buying option type (e.g., FIXED_PRICE, AUCTION)")
    matchCount: Optional[int] = Field(None, description="Number of items with this buying option")
    refinementHref: Optional[str] = Field(None, description="URL to refine search by this buying option")


class ConditionDistribution(BaseModel):
    """Distribution of item conditions"""
    condition: Optional[str] = Field(None, description="Condition name (e.g., NEW, USED)")
    conditionId: Optional[str] = Field(None, description="Condition identifier")
    matchCount: Optional[int] = Field(None, description="Number of items with this condition")
    refinementHref: Optional[str] = Field(None, description="URL to refine search by this condition")


class Refinement(BaseModel):
    """Refinement metadata for search results"""
    aspectDistributions: Optional[List[AspectDistribution]] = Field(
        None, 
        description="Distribution of item aspects (available with ASPECT_REFINEMENTS)"
    )
    buyingOptionDistributions: Optional[List[BuyingOptionDistribution]] = Field(
        None, 
        description="Distribution of buying options (available with BUYING_OPTION_REFINEMENTS)"
    )
    categoryDistributions: Optional[List[CategoryDistribution]] = Field(
        None, 
        description="Distribution across categories (available with CATEGORY_REFINEMENTS)"
    )
    conditionDistributions: Optional[List[ConditionDistribution]] = Field(
        None, 
        description="Distribution of conditions (available with CONDITION_REFINEMENTS)"
    )


class ItemSummarySearchResponse(BaseModel):
    """
    Response from the eBay item_summary/search endpoint.
    """
    
    href: Optional[str] = Field(None, description="URL of the current search request")
    total: Optional[int] = Field(None, description="Total number of items matching the search criteria")
    next: Optional[str] = Field(None, description="URL to retrieve the next page of results")
    prev: Optional[str] = Field(None, description="URL to retrieve the previous page of results")
    limit: Optional[int] = Field(None, description="Number of items returned in this response")
    offset: Optional[int] = Field(None, description="Number of items skipped before the first item in this response")
    itemSummaries: Optional[List[ItemSummary]] = Field(
        None, 
        description="Array of item summaries matching the search criteria"
    )
    refinement: Optional[Refinement] = Field(
        None, 
        description="Refinement metadata (available when using refinement fieldgroups)"
    )
    warnings: Optional[List[Dict[str, Any]]] = Field(None, description="Array of warnings, if any")


class EbayErrorResponse(BaseModel):
    """
    Error response from eBay API
    """
    
    errors: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Array of error details including category, domain, errorId, message, and parameters"
    )
    warnings: Optional[List[Dict[str, Any]]] = Field(None, description="Array of warnings, if any")

