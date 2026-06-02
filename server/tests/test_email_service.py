import pytest

from app.services import email as email_service


class FakeFastMail:
    sent_messages = []

    def __init__(self, conf):
        self.conf = conf

    async def send_message(self, message):
        self.sent_messages.append(message)


@pytest.mark.asyncio
async def test_send_price_drop_email_builds_html_message(monkeypatch: pytest.MonkeyPatch):
    FakeFastMail.sent_messages = []
    monkeypatch.setattr(email_service, "FastMail", FakeFastMail)

    await email_service.send_price_drop_email_async(
        to_email="buyer@example.com",
        product_name="iPhone 15",
        current_price=20_000_000,
        target_price=21_000_000,
    )

    message = FakeFastMail.sent_messages[0]
    assert message.subject == "🔥 Giá giảm: iPhone 15"
    assert message.recipients[0].email == "buyer@example.com"
    assert "iPhone 15" in message.body
    assert "20,000,000" in message.body


@pytest.mark.asyncio
async def test_send_password_reset_email_builds_html_message(monkeypatch: pytest.MonkeyPatch):
    FakeFastMail.sent_messages = []
    monkeypatch.setattr(email_service, "FastMail", FakeFastMail)

    await email_service.send_password_reset_email_async(
        to_email="buyer@example.com",
        reset_link="https://app.example/reset?token=abc",
    )

    message = FakeFastMail.sent_messages[0]
    assert message.subject == "Đặt lại mật khẩu ProductHunter"
    assert message.recipients[0].email == "buyer@example.com"
    assert "https://app.example/reset?token=abc" in message.body
