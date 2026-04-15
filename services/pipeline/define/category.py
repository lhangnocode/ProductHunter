"""
Canonical category definitions for the ProductHunter crawler.

`CATEGORIES` — master list of all valid category slugs (English, snake_case).
               Used by the LLM normalizer as the allowed value set for the
               "product_type" / "category" field.

`CATEGORY_LOCALE` — nested display-name map:
                    { en_slug: { "en": <English label>, "vi": <Vietnamese label> } }
                    Used for UI rendering and reporting.
"""
from typing import TypedDict


class CategoryLabel(TypedDict):
    en: str
    vi: str


CATEGORIES: list[str] = [
    # ── Must-have tech ───────────────────────────────────────────────────────
    "smartphone",       # required
    "laptop",           # required
    "tablet",           # required
    "desktop",          # required
    "monitor",          # required
    "headphone",        # required — covers both over-ear and in-ear
    "speaker",          # required
    "tv",               # required
    # ── Extended tech ────────────────────────────────────────────────────────
    "feature_phone",
    "pc_component",     # CPU, GPU, RAM, motherboard, PSU, etc.
    "storage",          # SSD, HDD, USB drive, memory card
    "peripheral",       # keyboard, mouse, mousepad, webcam
    "wearable",         # smart watch, fitness band
    "camera",           # DSLR, mirrorless, action cam, security cam
    "networking",       # router, switch, access point
    "power",            # charger, power bank, UPS
    "smart_home",
    "appliance",        # air conditioner, refrigerator, washing machine, etc.
    "houseware",        # smaller kitchen/household items
    "generic",
]

# Categories the LLM must prioritise — never fall back to "generic" for these
REQUIRED_CATEGORIES: set[str] = {
    "smartphone", "laptop", "tablet", "desktop",
    "monitor", "headphone", "speaker", "tv",
}

CATEGORY_LOCALE: dict[str, CategoryLabel] = {
    "smartphone":    {"en": "Smartphone",      "vi": "Điện thoại thông minh"},
    "feature_phone": {"en": "Feature Phone",   "vi": "Điện thoại phổ thông"},
    "tablet":        {"en": "Tablet",          "vi": "Máy tính bảng"},
    "laptop":        {"en": "Laptop",          "vi": "Máy tính xách tay"},
    "desktop":       {"en": "Desktop PC",      "vi": "Máy tính để bàn"},
    "monitor":       {"en": "Monitor",         "vi": "Màn hình máy tính"},
    "pc_component":  {"en": "PC Component",    "vi": "Linh kiện máy tính"},
    "storage":       {"en": "Storage",         "vi": "Thiết bị lưu trữ"},
    "peripheral":    {"en": "Peripheral",      "vi": "Thiết bị ngoại vi"},
    "headphone":     {"en": "Headphone",       "vi": "Tai nghe"},
    "speaker":       {"en": "Speaker",         "vi": "Loa"},
    "wearable":      {"en": "Wearable",        "vi": "Thiết bị đeo"},
    "camera":        {"en": "Camera",          "vi": "Máy ảnh / Camera"},
    "tv":            {"en": "TV",              "vi": "Tivi"},
    "networking":    {"en": "Networking",      "vi": "Thiết bị mạng"},
    "power":         {"en": "Power & Charging","vi": "Sạc & Pin dự phòng"},
    "smart_home":    {"en": "Smart Home",      "vi": "Nhà thông minh"},
    "appliance":     {"en": "Appliance",       "vi": "Đồ gia dụng lớn"},
    "houseware":     {"en": "Houseware",       "vi": "Đồ gia dụng nhỏ"},
    "generic":       {"en": "Other",           "vi": "Khác"}
}
