from app.agent.sales.objections import (
    build_objection_answers,
    detect_objections,
)


def test_detect_expensive():
    assert "expensive" in detect_objections("Sản phẩm này đắt quá")


def test_detect_cheaper_elsewhere_variations():
    assert "cheaper_elsewhere" in detect_objections("Bên CellphoneS rẻ hơn 500k")
    assert "cheaper_elsewhere" in detect_objections("Chỗ khác rẻ hơn nhiều")


def test_detect_authentic():
    assert "authentic" in detect_objections("Có phải hàng chính hãng không?")


def test_detect_multiple_objections():
    hits = detect_objections("Đắt quá, có trả góp không?")
    assert "expensive" in hits
    assert "installment" in hits


def test_no_objections_for_neutral_message():
    assert detect_objections("Cho tôi xem thông tin sản phẩm") == []


def test_answer_with_no_products_says_so():
    answers = build_objection_answers("Đắt quá", [], {})
    assert len(answers) == 1
    assert answers[0]["objection"] == "Đắt quá"
    assert "chưa có dữ liệu" in answers[0]["answer"]
    assert answers[0]["source_tool"]


def test_answer_cheap_elsewhere_picks_lowest_offer():
    products = [
        {
            "product_id": "p-1",
            "offers": [
                {"platform_name": "CellphoneS", "price": 9_500_000},
                {"platform_name": "FPT Shop", "price": 10_000_000},
            ],
        }
    ]
    answers = build_objection_answers("Bên FPT Shop rẻ hơn", products, {})
    assert len(answers) == 1
    assert "9,500,000đ" in answers[0]["answer"]
    assert "CellphoneS" in answers[0]["answer"]
