"""
Brand definitions and common product line keywords for the ProductHunter crawler.

`BRANDS` — canonical brand name list (Title Case).

`BRAND_MODELS` — maps each brand to its most recognisable product line keywords.
                 Kept deliberately short so this can be embedded directly in
                 an LLM prompt as context for brand/model identification.
"""

BRANDS: list[str] = [
    "Apple", "Samsung", "Xiaomi", "Redmi", "POCO",
    "Oppo", "Vivo", "Realme", "OnePlus", "Huawei", "Honor",
    "Nokia", "Sony", "Motorola", "Asus", "Lenovo",
    "Dell", "HP", "Acer", "MSI", "Microsoft",
    "LG", "TCL", "Hisense", "Philips",
    "JBL", "Bose", "Sennheiser", "Beats", "Marshall",
    "Canon", "Nikon", "Fujifilm", "GoPro", "DJI",
    "Intel", "AMD", "Nvidia", "Kingston", "Corsair",
    "TP-Link", "D-Link", "Netgear",
    "Generic",
]

# keyword → brand  (common product line names that imply a brand)
BRAND_MODELS: dict[str, str] = {
    # Apple
    "iPhone":       "Apple",
    "iPad":         "Apple",
    "MacBook":      "Apple",
    "iMac":         "Apple",
    "AirPods":      "Apple",
    "Apple Watch":  "Apple",

    # Samsung
    "Galaxy S":     "Samsung",
    "Galaxy Z Fold":"Samsung",
    "Galaxy Z Flip":"Samsung",
    "Galaxy A":     "Samsung",
    "Galaxy Tab":   "Samsung",
    "Galaxy Book":  "Samsung",
    "Galaxy Watch": "Samsung",
    "Galaxy Buds":  "Samsung",

    # Xiaomi / sub-brands
    "Redmi Note":   "Redmi",
    "POCO X":       "POCO",
    "POCO M":       "POCO",
    "POCO F":       "POCO",

    # Oppo
    "Find X":       "Oppo",
    "Reno":         "Oppo",

    # Vivo / iQOO
    "iQOO":         "Vivo",

    # OnePlus
    "Nord":         "OnePlus",

    # Huawei
    "Mate":         "Huawei",
    "Nova":         "Huawei",
    "MatePad":      "Huawei",
    "MateBook":     "Huawei",
    "FreeBuds":     "Huawei",

    # Sony
    "Xperia":       "Sony",
    "WH-1000":      "Sony",
    "WF-1000":      "Sony",
    "Bravia":       "Sony",

    # Asus
    "ROG Phone":    "Asus",
    "ROG Zephyrus": "Asus",
    "ROG Strix":    "Asus",
    "ZenBook":      "Asus",
    "VivoBook":     "Asus",

    # Lenovo
    "ThinkPad":     "Lenovo",
    "IdeaPad":      "Lenovo",
    "Legion":       "Lenovo",
    "Yoga":         "Lenovo",

    # Dell
    "XPS":          "Dell",
    "Inspiron":     "Dell",
    "Alienware":    "Dell",

    # HP
    "Spectre":      "HP",
    "Envy":         "HP",
    "Omen":         "HP",
    "Victus":       "HP",
    "Pavilion":     "HP",

    # Acer
    "Swift":        "Acer",
    "Aspire":       "Acer",
    "Nitro":        "Acer",
    "Predator":     "Acer",

    # Microsoft
    "Surface Pro":  "Microsoft",
    "Surface Laptop":"Microsoft",

    # Audio
    "QuietComfort": "Bose",
    "SoundLink":    "Bose",
    "Momentum":     "Sennheiser",

    # Camera / Drone
    "EOS":          "Canon",
    "Mavic":        "DJI",
    "Mini":         "DJI",
    "Osmo":         "DJI",
}
