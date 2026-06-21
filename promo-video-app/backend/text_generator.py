import re
from typing import List, Dict, Tuple

# Style keywords mapped to categories
STYLE_KEYWORDS = {
    "luxury": ["luxury", "luxe", "premium", "exclusif", "exclusive", "high-end", "prestige", "élégant", "elegant", "sophistiqué"],
    "hype": ["hype", "fire", "lit", "banger", "hype", "trending", "viral", "drop", "flex"],
    "california": ["california", "californien", "beach", "plage", "summer", "été", "surf", "chill", "vibes"],
    "fashion": ["fashion", "mode", "style", "outfit", "look", "tendance", "collection", "wear"],
    "sport": ["sport", "fitness", "gym", "training", "performance", "athletic", "workout"],
    "food": ["food", "restaurant", "cuisine", "chef", "délicieux", "tasty", "gastro"],
    "tech": ["tech", "digital", "innovation", "smart", "futuriste"],
    "fast": ["rapide", "fast", "cuts", "dynamique", "energetic", "énergique", "intense"],
}

TEXT_TEMPLATES: Dict[str, List[Tuple[str, str]]] = {
    "luxury": [
        ("LUXURY\nCOLLECTION", "SHOP NOW"),
        ("EXCLUSIVE\nDROPS", "LIMITED EDITION"),
        ("PREMIUM\nQUALITY", "DISCOVER MORE"),
        ("NEW\nARRIVALS", "ONLY THE BEST"),
        ("ICONIC\nSTYLE", "BE DIFFERENT"),
    ],
    "hype": [
        ("THE\nDROP 🔥", "GET YOURS"),
        ("LIMITED\nSTOCK", "ORDER NOW"),
        ("TRENDING\nNOW", "DON'T MISS OUT"),
        ("SOLD OUT\nSOON ⚡", "HURRY UP"),
        ("NEW\nSEASON", "FIRE COLLECTION"),
    ],
    "california": [
        ("CALIFORNIA\nVIBES ☀️", "FEEL THE ENERGY"),
        ("SUMMER\nDROP", "BEACH READY"),
        ("WEST COAST\nSTYLE", "LIVE FREE"),
        ("SUN &\nSTYLE", "SHOP NOW"),
    ],
    "fashion": [
        ("NEW\nCOLLECTION", "STYLE UP"),
        ("THIS\nSEASON", "MUST HAVE"),
        ("WEAR\nYOUR STORY", "DISCOVER"),
        ("MADE FOR\nYOU", "SHOP NOW"),
    ],
    "sport": [
        ("PUSH YOUR\nLIMITS", "TRAIN HARDER"),
        ("PERFORMANCE\nGEAR", "LEVEL UP"),
        ("NO EXCUSES\n💪", "GET MOVING"),
    ],
    "food": [
        ("TASTE THE\nDIFFERENCE", "ORDER NOW"),
        ("CRAFTED\nWITH LOVE ❤️", "DISCOVER"),
        ("DELICIOUS\nEVERY DAY", "TASTE NOW"),
    ],
    "tech": [
        ("NEXT LEVEL\nTECH", "EXPLORE"),
        ("FUTURE IS\nNOW", "DISCOVER"),
        ("SMART\nLIVING", "UPGRADE"),
    ],
    "default": [
        ("NEW\nCOLLECTION", "SHOP NOW"),
        ("DISCOVER\nNOW", "EXPLORE MORE"),
        ("MADE FOR\nYOU", "GET YOURS"),
        ("LIMITED\nEDITION", "ORDER TODAY"),
    ],
}


def detect_style(description: str) -> str:
    desc_lower = description.lower()
    scores = {style: 0 for style in STYLE_KEYWORDS}

    for style, keywords in STYLE_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                scores[style] += 1

    best_style = max(scores, key=scores.get)
    if scores[best_style] == 0:
        return "default"
    return best_style


def extract_product_name(description: str) -> str:
    # Try to extract a product keyword for personalized text
    product_patterns = [
        r'\b(bag|bags|sac|sacs|purse|purses)\b',
        r'\b(shoe|shoes|chaussure|chaussures|sneaker|sneakers)\b',
        r'\b(watch|watches|montre|montres)\b',
        r'\b(dress|dresses|robe|robes)\b',
        r'\b(jacket|jackets|veste|vestes)\b',
        r'\b(perfume|parfum|fragrance)\b',
        r'\b(jewelry|bijoux|ring|necklace)\b',
        r'\b(phone|iphone|smartphone)\b',
    ]
    desc_lower = description.lower()
    for pattern in product_patterns:
        match = re.search(pattern, desc_lower)
        if match:
            return match.group(1).upper()
    return ""


def detect_text_style(description: str) -> Dict:
    desc_lower = description.lower()
    style = {
        "font_color": "white",
        "font_size": 80,
        "font_weight": "bold",
        "position": "center",
        "stroke_width": 3,
        "stroke_color": "black",
    }

    if "blanc" in desc_lower or "white" in desc_lower:
        style["font_color"] = "white"
    elif "noir" in desc_lower or "black" in desc_lower:
        style["font_color"] = "black"
    elif "doré" in desc_lower or "gold" in desc_lower:
        style["font_color"] = "#FFD700"
    elif "rose" in desc_lower or "pink" in desc_lower:
        style["font_color"] = "#FF69B4"

    if "gras" in desc_lower or "bold" in desc_lower:
        style["font_size"] = 90
        style["stroke_width"] = 4

    if "petit" in desc_lower or "small" in desc_lower:
        style["font_size"] = 60

    if "bas" in desc_lower or "bottom" in desc_lower:
        style["position"] = "bottom"
    elif "haut" in desc_lower or "top" in desc_lower:
        style["position"] = "top"

    return style


def generate_text_overlays(description: str, num_images: int) -> List[Dict]:
    style = detect_style(description)
    product = extract_product_name(description)
    text_style = detect_text_style(description)
    templates = TEXT_TEMPLATES.get(style, TEXT_TEMPLATES["default"])

    # Select a subset of overlays based on video length
    num_overlays = min(num_images, len(templates), 4)
    selected = templates[:num_overlays]

    overlays = []
    for i, (main_text, cta_text) in enumerate(selected):
        # Personalize if we detected a product
        if product and "{PRODUCT}" in main_text:
            main_text = main_text.replace("{PRODUCT}", product)

        overlays.append({
            "main_text": main_text,
            "cta_text": cta_text,
            "style": text_style,
            "image_index": i,  # show on which image clip
        })

    return overlays
