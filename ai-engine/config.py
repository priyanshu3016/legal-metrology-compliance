"""
Configuration and constants for the Legal Metrology Compliance AI Engine.
"""

from typing import List, Dict

# The 9 mandatory declaration fields required under
# Legal Metrology (Packaged Commodities) Rules, 2011
FIELD_PRODUCT_NAME = "product_name"
FIELD_MANUFACTURER = "manufacturer_packer_importer"
FIELD_NET_QUANTITY = "net_quantity"
FIELD_MRP = "mrp"
FIELD_MFG_DATE = "manufacturing_date"
FIELD_CONSUMER_CARE = "consumer_care"
FIELD_COUNTRY_OF_ORIGIN = "country_of_origin"
FIELD_BEST_BEFORE = "best_before"
FIELD_UNIT_SALE_PRICE = "unit_sale_price"

MANDATORY_FIELDS: List[str] = [
    FIELD_PRODUCT_NAME,
    FIELD_MANUFACTURER,
    FIELD_NET_QUANTITY,
    FIELD_MRP,
    FIELD_MFG_DATE,
    FIELD_CONSUMER_CARE,
    FIELD_COUNTRY_OF_ORIGIN,
    FIELD_BEST_BEFORE,
    FIELD_UNIT_SALE_PRICE,
]

FIELD_LABELS: Dict[str, str] = {
    FIELD_PRODUCT_NAME: "Product Name",
    FIELD_MANUFACTURER: "Manufacturer / Packer / Importer",
    FIELD_NET_QUANTITY: "Net Quantity",
    FIELD_MRP: "Maximum Retail Price",
    FIELD_MFG_DATE: "Manufacturing / Packing Date",
    FIELD_CONSUMER_CARE: "Consumer Care Details",
    FIELD_COUNTRY_OF_ORIGIN: "Country of Origin",
    FIELD_BEST_BEFORE: "Best Before / Use By",
    FIELD_UNIT_SALE_PRICE: "Unit Sale Price",
}

# OCR Filtering & Extraction Thresholds
DEFAULT_OCR_MIN_CONFIDENCE = 0.30
DETECTION_CONFIDENCE_THRESHOLD = 0.60

# Image Preprocessing Constraints
IMAGE_MIN_DIMENSION = 640
IMAGE_MAX_DIMENSION = 4000
IMAGE_TARGET_SHORT_EDGE = 1000

# Supported image file formats
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Multi-image inspection roles
IMAGE_ROLE_FRONT = "front"
IMAGE_ROLE_BACK = "back"
IMAGE_ROLE_SIDE = "side"
IMAGE_ROLES_REQUIRED = [IMAGE_ROLE_FRONT, IMAGE_ROLE_BACK]
IMAGE_ROLES_ALL = [IMAGE_ROLE_FRONT, IMAGE_ROLE_BACK, IMAGE_ROLE_SIDE]

