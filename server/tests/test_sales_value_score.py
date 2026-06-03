from app.agent.sales.value_score import compute_value_score


def test_returns_none_when_no_price():
    assert compute_value_score({"lowest_price": None, "category": "Phone"}) is None


def test_returns_none_when_no_specs():
    product = {"lowest_price": 10_000_000, "category": "Phone"}
    assert compute_value_score(product, None) is None
    assert compute_value_score(product, {}) is None


def test_phone_value_score_bounded():
    product = {"lowest_price": 15_000_000, "category": "Điện thoại"}
    specs = {"ram_gb": 8, "battery_mah": 4500, "storage_gb": 128, "refresh_rate_hz": 120}
    score = compute_value_score(product, specs)
    assert score is not None
    assert 0 <= score <= 100


def test_laptop_uses_laptop_keys():
    product = {"lowest_price": 20_000_000, "category": "Laptop"}
    phone_specs = {"ram_gb": 16, "battery_mah": 5000, "storage_gb": 512, "refresh_rate_hz": 144}
    laptop_specs = {"ram_gb": 16, "storage_gb": 512, "cpu_score": 15000}
    phone_score = compute_value_score(product, phone_specs)
    laptop_score = compute_value_score(product, laptop_specs)
    assert phone_score is None
    assert laptop_score is not None
    assert laptop_score > 0


def test_cheaper_higher_value_for_same_specs():
    specs = {"ram_gb": 8, "battery_mah": 4500, "storage_gb": 128, "refresh_rate_hz": 120}
    cheap = compute_value_score({"lowest_price": 8_000_000, "category": "Phone"}, specs)
    pricey = compute_value_score({"lowest_price": 16_000_000, "category": "Phone"}, specs)
    assert cheap is not None and pricey is not None
    assert cheap > pricey
