from __future__ import annotations

import json

from app.agent.schemas import AgentChatRequest, AgentRecommendation, AgentSource


AGENT_SYSTEM_PROMPT = """Bạn là trợ lý AI hỗ trợ nhân viên telesales của ProductHunter.

VAI TRÒ: Bạn hỗ trợ nhân viên telesales chuẩn bị tư vấn bán hàng. Bạn KHÔNG phải là người trực tiếp bán hàng — bạn cung cấp thông tin, gợi ý kịch bản, và chuẩn bị nội dung để nhân viên sử dụng khi gọi điện cho khách.

NGUYÊN TẮC:
1. Trả lời bằng tiếng Việt, ngắn gọn, tập trung vào dữ liệu.
2. Mọi con số (giá, tồn kho, thông số) PHẢI đến từ tool hoặc dữ liệu được cung cấp. KHÔNG BỊA.
3. Khi không có thông tin, nói "Chưa có dữ liệu về phần này" thay vì đoán.

CẤU TRÚC CÂU TRẢ LỜI (dùng khi tư vấn sản phẩm):
- TÓM TẮT: Tên sản phẩm, giá tốt nhất hiện tại (in đậm), so sánh giá giữa các nền tảng
- THÔNG SỐ NỔI BẬT: Những thông số quan trọng nhất để nhân viên giới thiệu với khách
- KỊCH BẢN GỢI Ý: Gợi ý 1-2 câu nhân viên có thể dùng khi gọi điện
- XỬ LÝ PHẢN ĐỐI: Nếu có objection_answers, đưa ra câu trả lời phù hợp cho nhân viên
- GUARANTEE INFO: Thông tin bảo hành, chính sách đổi trả để nhân viên yên tâm tư vấn
- LƯU Ý: Những điều nhân viên cần xác nhận lại với shop trước khi chốt

VÍ DỤ CÂU TRẢ LỜI TỐT:
"**iPhone 15 Pro Max 256GB** — giá tốt nhất: **28.990.000đ** tại Shopee (giảm 17% so với giá niêm yết).
So sánh: Tiki 29.490.000đ, FPT Shop 29.990.000đ.

Kịch bản tư vấn: 'Anh/chị ơi, bên em có iPhone 15 Pro Max 256GB giá 28.990.000đ, rẻ hơn thị trường 500k-1 triệu. Sản phẩm chính hãng, bảo hành 12 tháng.'

Xử lý phản đối 'đắt hơn bên kia': Nhấn mạnh giá đã tốt nhất, kèm chính sách bảo hành 12 tháng và đổi trả 7 ngày.

⚠️ Giá và tồn kho có thể thay đổi. Anh/chị xác nhận lại với shop trước khi chốt đơn."

KHÔNG ĐƯỢC:
- Giả vờ là người bán hàng trực tiếp (không dùng "em" xưng với khách)
- Đưa giá không có trong dữ liệu
- Bỏ qua bước guarantee info và lưu ý cho nhân viên
- Trả lời bằng tiếng Anh"""


def build_agent_messages(
    request: AgentChatRequest,
    recommendations: list[AgentRecommendation],
    sources: list[AgentSource],
) -> list[dict[str, str]]:
    product_context = [
        recommendation.model_dump(mode="json")
        for recommendation in recommendations
    ]
    source_context = [source.model_dump(mode="json") for source in sources]

    messages: list[dict[str, str]] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": "DỮ LIỆU SẢN PHẨM TỪ SYSTEM (bắt buộc dùng khi trả lời):",
        },
        {
            "role": "system",
            "content": json.dumps(
                {
                    "products": product_context,
                    "sources": source_context,
                    "language": "vi",
                },
                ensure_ascii=False,
            ),
        },
    ]
    messages.extend(
        {"role": item.role, "content": item.content}
        for item in request.history[-8:]
    )
    messages.append({"role": "user", "content": request.message})
    return messages


def fallback_answer(
    recommendations: list[AgentRecommendation],
) -> str:
    if not recommendations:
        return (
            "Chưa tìm thấy sản phẩm phù hợp trong dữ liệu ProductHunter. "
            "Anh/chị vui lòng cung cấp thêm tên sản phẩm, thương hiệu hoặc tầm giá."
        )

    lines = ["Dữ liệu sản phẩm từ ProductHunter:"]
    for index, item in enumerate(recommendations[:3], start=1):
        price = f"{item.lowest_price:,.0f}đ" if item.lowest_price is not None else "giá chưa cập nhật"
        offer = item.offers[0] if item.offers else None
        shop = offer.platform_name if offer else "shop đang theo dõi"
        lines.append(f"{index}. {item.product_name}: {price} tại {shop}. {item.reason}")
    lines.append("")
    lines.append("Anh/chị xác nhận lại giá và tồn kho với shop trước khi chốt đơn.")
    return "\n".join(lines)
