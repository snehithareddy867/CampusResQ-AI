"""Map AI incident categories to configured helping-team departments.

AI never writes arbitrary team IDs. Only values from CATEGORY_TO_DEPARTMENT
are persisted as assigned_department.
"""
from typing import Dict

# Controlled categories produced by the analyzer (uppercase).
ALLOWED_CATEGORIES = (
    "MEDICAL",
    "FIRE",
    "SECURITY",
    "ACCIDENT",
    "TECHNICAL",
    "ELECTRICAL",
    "WATER",
    "RESCUE",
    "OTHER",
    "CONSTRUCTION",
    "ENVIRONMENTAL",
    "TRANSPORT",
    "FACILITIES",
)

# Existing Mongo/user department values (backend.models.Department).
CATEGORY_TO_DEPARTMENT = {
    "MEDICAL": "medical",
    "FIRE": "fire_safety",
    "SECURITY": "security",
    "ACCIDENT": "medical",
    "ELECTRICAL": "electrical",
    "WATER": "facilities",
    "TECHNICAL": "facilities",
    "RESCUE": "security",
    "OTHER": "security",
    "CONSTRUCTION": "construction",
    "ENVIRONMENTAL": "environmental",
    "TRANSPORT": "transport",
    "FACILITIES": "facilities",
}

TEAM_DISPLAY_NAMES = {
    "medical": "Medical Team",
    "fire_safety": "Fire/Safety Team",
    "security": "Security Team",
    "electrical": "Electrical Team",
    "construction": "Construction Team",
    "facilities": "Facilities / Maintenance Team",
    "environmental": "Environmental Team",
    "transport": "Transport Team",
}


def normalize_category(raw: str) -> str:
    if not raw:
        return "OTHER"
    key = str(raw).strip().upper().replace(" ", "_").replace("-", "_")
    aliases = {
        "FIRE_SAFETY": "FIRE",
        "FIRESAFETY": "FIRE",
        "MED": "MEDICAL",
        "MAINTENANCE": "FACILITIES",
        "PLUMBING": "WATER",
        "FLOOD": "WATER",
        "THEFT": "SECURITY",
        "ASSAULT": "SECURITY",
        "CRASH": "ACCIDENT",
        "VEHICLE": "TRANSPORT",
        "GAS": "FIRE",
        "SMOKE": "FIRE",
    }
    key = aliases.get(key, key)
    if key in CATEGORY_TO_DEPARTMENT:
        return key
    return "OTHER"


def route_category(category: str) -> Dict[str, str]:
    """Return department id + display name for a validated category."""
    cat = normalize_category(category)
    dept = CATEGORY_TO_DEPARTMENT[cat]
    return {
        "category": cat,
        "department": dept,
        "team_name": TEAM_DISPLAY_NAMES.get(dept, dept.replace("_", " ").title() + " Team"),
    }
