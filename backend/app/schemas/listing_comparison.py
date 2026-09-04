from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

class EcomListingPayload(BaseModel):
    """
    Metadata / attributes extracted from an e-commerce marketplace listing screenshot or product page.
    """
    marketplace_name: Optional[str] = Field(None, description="Platform name (e.g. Amazon, Flipkart, Blinkit, Zepto)")
    listed_title: Optional[str] = Field(None, description="Product title on the digital listing")
    listed_price: Optional[str] = Field(None, description="Selling price or MRP declared on the listing")
    listed_net_quantity: Optional[str] = Field(None, description="Net quantity declared in the listing specification")
    listed_country_of_origin: Optional[str] = Field(None, description="Country of origin declared on listing")
    listed_manufacturer: Optional[str] = Field(None, description="Manufacturer/seller declared on listing")
    listing_url: Optional[str] = Field(None, description="Product listing URL if available")

    model_config = ConfigDict(from_attributes=True)

class ListingComparisonResult(BaseModel):
    inspection_id: str
    has_listing: bool
    listing_attributes: Optional[EcomListingPayload] = None
    discrepancies: List[str] = Field(default_factory=list)
    status: str = Field(..., description="COMPLIANT, POTENTIAL_DISCREPANCY, NOT_APPLICABLE")

    model_config = ConfigDict(from_attributes=True)
