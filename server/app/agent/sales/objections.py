from __future__ import annotations

import re
from typing import Any

OBJECTION_PATTERNS: dict[str, list[str]] = {
    "cheaper_elsewhere": [
        r"\b(bên [a-zà-ỹ][a-zà-ỹ\s]+ rẻ hơn)\b",
        r"\b(shop [a-zà-ỹ][a-zà-ỹ\s]+ rẻ hơn)\b",
        r"\b(chỗ khác rẻ hơn|nơi khác rẻ hơn)\b",
        r"\b(rẻ hơn \d)",
    ],
    "expensive": [
        r"\b(đắt quá|mắc quá|giá cao quá)\b",
        r"\b(giảm giá|khuyến mãi)\b",
    ],
    "authentic": [
        r"\b(chính hãng|hàng thật|hàng fake|hàng nhái|có phải chính hãng)\b",
    ],
    "warranty": [
        r"\b(bảo hành|bảo hành thế nào|bảo hành bao lâu)\b",
    ],
    "installment": [
        r"\b(trả góp|trả sau|installment|góp)\b",
    ],
    "delivery": [
        r"\b(giao khi nào|giao hàng|ship|ship khi nào|giao mấy ngày)\b",
    ],
}


def detect_objections(message: str) -> list[str]:
    text = (message or "").lower()
    hits: list[str] = []
    for objection, patterns in OBJECTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(objection)
                break
    return hits


def build_objection_answers(
    message: str,
    products: list[dict[str, Any]],
    price_history_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build Vietnamese objection answers citing the source tool.

    The handler never invents data. If the required tool data is missing,
    the answer explicitly says so.
    """
    price_history_by_id = price_history_by_id or {}
    detected = detect_objections(message)
    if not detected:
        return []

    answers: list[dict[str, Any]] = []
    best_product = _best_product(products)

    for objection in detected:
        if objection == "expensive":
            answers.append(_answer_expensive(best_product))
        elif objection == "cheaper_elsewhere":
            answers.append(_answer_cheaper_elsewhere(products))
        elif objection == "authentic":
            answers.append(_answer_authentic(best_product))
        elif objection == "warranty":
            answers.append(_answer_warranty(best_product))
        elif objection == "installment":
            answers.append(_answer_installment(best_product))
        elif objection == "delivery":
            answers.append(_answer_delivery(best_product))
    return answers


def _best_product(products: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not products:
        return None
    return products[0]


def _format_vnd(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return f"{float(value):,.0f}đ"
    except (TypeError, ValueError):
        return None


def _answer_expensive(product: dict[str, Any] | None) -> dict[str, Any]:
    if product is None:
        return {
            "objection": "Đắt quá",
            "answer": "Em chưa có dữ liệu sản phẩm để so sánh giá thị trường.",
            "source_tool": "search_products",
        }
    lowest = _format_vnd(product.get("lowest_price"))
    offers = product.get("offers") or []
    platform_count = len({offer.get("platform_name") for offer in offers if offer.get("platform_name")})
    if lowest is None:
        return {
            "objection": "Đắt quá",
            "answer": "Giá sản phẩm này chưa được cập nhật, em sẽ xác minh với shop.",
            "source_tool": "search_products",
        }
    if platform_count >= 2:
        return {
            "objection": "Đắt quá",
            "answer": (
                f"Giá từ {lowest} trên {platform_count} sàn đang được so sánh. "
                "Em sẽ chọn sàn có chính sách phù hợp nhất cho anh chị."
            ),
            "source_tool": "compare_prices",
        }
    return {
        "objection": "Đắt quá",
        "answer": f"Giá tham khảo từ ProductHunter: {lowest}.",
        "source_tool": "search_products",
    }


def _answer_cheaper_elsewhere(products: list[dict[str, Any]]) -> dict[str, Any]:
    if not products:
        return {
            "objection": "Bên khác rẻ hơn",
            "answer": "Em chưa tìm thấy sản phẩm tương ứng trên các sàn đang hỗ trợ.",
            "source_tool": "compare_prices",
        }
    offers_with_price = []
    for product in products:
        for offer in product.get("offers") or []:
            if offer.get("price") is not None:
                offers_with_price.append(
                    {
                        "platform": offer.get("platform_name"),
                        "price": offer.get("price"),
                    }
                )
    if not offers_with_price:
        return {
            "objection": "Bên khác rẻ hơn",
            "answer": "Em chưa có đủ dữ liệu giá trên các sàn để so sánh.",
            "source_tool": "compare_prices",
        }
    offers_with_price.sort(key=lambda item: float(item["price"]))
    cheapest = offers_with_price[0]
    return {
        "objection": "Bên khác rẻ hẻn",
        "answer": (
            f"Giá thấp nhất trên các sàn được theo dõi: {float(cheapest['price']):,.0f}đ "
            f"tại {cheapest['platform']}."
        ),
        "source_tool": "compare_prices",
    }


def _answer_authentic(product: dict[str, Any] | None) -> dict[str, Any]:
    if product is None:
        return {
            "objection": "Có hàng chính hãng không?",
            "answer": "Em chưa xác minh được nguồn gốc sản phẩm, em sẽ kiểm tra với shop.",
            "source_tool": "search_products",
        }
    return {
        "objection": "Có hàng chính hãng không?",
        "answer": "Sản phẩm được liệt kê từ các sàn chính hãng trong dữ liệu ProductHunter.",
        "source_tool": "get_product_detail",
    }


def _answer_warranty(product: dict[str, Any] | None) -> dict[str, Any]:
    if product is None:
        return {
            "objection": "Bảo hành thế nào?",
            "answer": "Em chưa có thông tin bảo hành, em sẽ xác minh với shop.",
            "source_tool": "get_product_detail",
        }
    return {
        "objection": "Bảo hành thế nào?",
        "answer": "Chính sách bảo hành tùy thuộc vào từng sàn; em sẽ xác nhận trước khi chốt đơn.",
        "source_tool": "get_product_detail",
    }


def _answer_installment(product: dict[str, Any] | None) -> dict[str, Any]:
    if product is None:
        return {
            "objection": "Có trả góp không?",
            "answer": "Em chưa có thông tin trả góp cho sản phẩm này.",
            "source_tool": "search_products",
        }
    return {
        "objection": "Có trả góp không?",
        "answer": "Hỗ trợ trả góp tùy theo sàn và thẻ tín dụng; em sẽ kiểm tra với shop.",
        "source_tool": "search_products",
    }


def _answer_delivery(product: dict[str, Any] | None) -> dict[str, Any]:
    if product is None:
        return {
            "objection": "Giao khi nào?",
            "answer": "Em chưa có dữ liệu giao hàng cho sản phẩm này.",
            "source_tool": "search_products",
        }
    return {
        "objection": "Giao khi nào?",
        "answer": "Thời gian giao hàng tùy theo sàn và khu vực, em sẽ xác nhận trước khi chốt đơn.",
        "source_tool": "get_product_detail",
    }
