from __future__ import annotations

import json

from app.agent.schemas import AgentChatRequest, AgentRecommendation, AgentSource


AGENT_SYSTEM_PROMPT = (
    "Bạn là trợ lý tư vấn bán hàng cho ProductHunter, phục vụ nhân viên telesales. "
    "Trả lời bằng tiếng Việt, giọng lịch sự, dùng 'em' khi nói với khách, ngắn gọn và thực tế. "
    "Mọi con số về giá, tồn kho, bảo hành và thông số phải đến từ tool; không bịa. "
    "Khi tool trả null, hãy nói 'em chưa có thông tin này' thay vì đoán. "
    "Cấu trúc câu trả lời: gợi ý chính, bằng chứng (giá/spec/ưu đãi), nguồn, disclaimer. "
    "Không so sánh sản phẩm ngoài danh sách tool trả về. "
    "Khi khách phản đối, dùng objection_answers được cung cấp."
)


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
            "Em chưa tìm thấy sản phẩm phù hợp trong dữ liệu ProductHunter. "
            "Anh chị cho em biết thêm tên sản phẩm, thương hiệu hoặc tầm giá nhé."
        )

    lines = ["Gợi ý từ ProductHunter:"]
    for index, item in enumerate(recommendations[:3], start=1):
        price = f"{item.lowest_price:,.0f}đ" if item.lowest_price is not None else "giá chưa cập nhật"
        offer = item.offers[0] if item.offers else None
        shop = offer.platform_name if offer else "shop đang theo dõi"
        lines.append(f"{index}. {item.product_name}: {price} tại {shop}. {item.reason}")
    lines.append("Anh chị xác nhận lại giá và tồn kho với shop trước khi chốt đơn.")
    return "\n".join(lines)
