from app.agent.sales.trust import build_trust, trust_to_vietnamese


def test_returns_none_when_data_missing():
    product = {"product_name": "Phone"}
    offer = {"platform_name": "CellphoneS"}
    trust = build_trust(product, offer)
    assert trust == {"warranty_months": None, "is_authentic": None, "return_days": None}


def test_reads_from_offer_first():
    product = {"warranty_months": 6}
    offer = {"warranty_months": 12, "is_authentic": True}
    trust = build_trust(product, offer)
    assert trust["warranty_months"] == 12
    assert trust["is_authentic"] is True


def test_trust_to_vietnamese_renders_lines():
    trust = {"warranty_months": 12, "is_authentic": True, "return_days": 30}
    lines = trust_to_vietnamese(trust)
    assert any("chính hãng" in line for line in lines)
    assert any("Bảo hành 12 tháng" in line for line in lines)
    assert any("Đổi trả trong 30 ngày" in line for line in lines)


def test_trust_to_vietnamese_handles_unverified():
    lines = trust_to_vietnamese({"is_authentic": False, "warranty_months": None, "return_days": None})
    assert any("cần xác minh" in line for line in lines)
