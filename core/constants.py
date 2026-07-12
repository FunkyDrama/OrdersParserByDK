"""The single source of project constants.

Column names, sheet names, the color palette and the wallpaper regex used to
be scattered across gsheet_writer.py and the parsers.
"""

import re

APP_VERSION = "7.2.3"
APP_TITLE = f"Orders Parser v{APP_VERSION} by Daniel K"

# --- Marker values (used by all parsers) ---
ERROR_VALUE = "!ERROR!"
FILE_NOT_FOUND = "File Not Found"

# --- Google Sheets columns ---
COL_STATUS = "Status"
COL_ADDITIONAL_INFO = "Additional Info"
COL_DATE = "Date"
COL_STORE = "Store"
COL_CHANNEL = "Channel"
COL_SKU = "ASIN/SKU"
COL_LISTING_LINK = "Listing Link"
COL_ORDER_ID = "Order ID"
COL_TITLE = "Title"
COL_ADDRESS = "Address/Ship to"
COL_QUANTITY = "Quantity"
COL_CUSTOMIZATION = "Customization info"
COL_FILE_LINK = "File Link"
COL_SHIPPING_LABEL = "Shipping label link"
COL_TRACK_ID = "Track ID"
COL_SHIP_BY = "Ship By"
COL_POSTAL_SERVICE = "Postal Service"
COL_SHIPPING_SPEED = "Shipping speed"
COL_TRACK_PACKAGE = "Track package"
COL_ITEMS_TOTAL = "Items total"
COL_SHIPPING_TOTAL = "Shipping total"
COL_SHIPPING_PRICE = "Shipping price"
COL_TOTAL = "Total"

# Columns highlighted with the order color for multi-item orders
HIGHLIGHT_COLUMNS = [COL_ORDER_ID, COL_ADDRESS, COL_SHIPPING_LABEL, COL_TRACK_ID]

# Columns merged vertically for multi-item orders
MERGE_COLUMNS = [
    COL_POSTAL_SERVICE,
    COL_SHIPPING_SPEED,
    COL_TRACK_PACKAGE,
    COL_ITEMS_TOTAL,
    COL_SHIPPING_TOTAL,
    COL_SHIPPING_PRICE,
    COL_TOTAL,
]

# --- Spreadsheet sheets ---
SHEET_WALLPAPER = "Wallpaper"
SHEET_COLORED = "Colored"
SHEET_22_ROLL = "22 roll"
SHEET_46_ROLL = "46 roll"
SHEET_ERROR = "ERROR"

# Extensions of "colored" files (routed to the Colored sheet)
COLORED_EXTENSIONS = {"png", "jpg", "jpeg", "eps"}

# Smaller-side threshold for roll routing, inches
ROLL_SIZE_THRESHOLD = 22

# --- Highlight palette for multi-item orders (RGB 0..1) ---
MULTI_ITEM_PALETTE: list[tuple[float, float, float]] = [
    (0.55, 0.80, 1.00),
    (0.55, 1.00, 0.55),
    (1.00, 0.55, 0.55),
    (0.70, 0.55, 1.00),
    (1.00, 0.75, 0.40),
    (0.45, 1.00, 0.80),
    (1.00, 0.55, 0.85),
    (0.55, 0.95, 1.00),
    (0.60, 1.00, 0.40),
    (1.00, 0.60, 0.40),
]

STATUS_CELL_COLOR = {"red": 1.0, "green": 0.0, "blue": 0.0}

# --- Parcel tracking links ---
TRACKING_URL_TEMPLATES: dict[str, str] = {
    "USPS": "https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1={number}",
    "UPS": (
        "https://www.ups.com/track?TypeOfInquiryNumber=T&InquiryNumber1={number}"
        "&loc=en_US&requester=ST/trackdetails"
    ),
    "FedEx": "https://www.fedex.com/apps/fedextrack/?tracknumbers={number}",
    "DHL": (
        "https://www.dhl.com/us-en/home/tracking/tracking-express.html"
        "?submit=1&tracking-id={number}"
    ),
}
# UPS sometimes arrives as "UPS®"
TRACKING_URL_TEMPLATES["UPS®"] = TRACKING_URL_TEMPLATES["UPS"]

DATE_FORMAT = "%d.%m.%Y"

# How many days to keep file logs (older ones are removed at startup)
LOG_RETENTION_DAYS = 3

# --- Wallpaper: Peel & Stick / Non-Woven (moved verbatim from gsheet_writer) ---
WALLPAPER_PATTERN = re.compile(
    r"""(?ix)
    (
        # Peel & Stick
        pe[e]?l
        \s*[-&]?\s*
        (?:n|and)?
        \s*[-&]?\s*
        stick

        |

        # Non-Woven
        non
        \s*[-]?\s*
        woven
        (?:\s*fabric)?
    )
    """
)
