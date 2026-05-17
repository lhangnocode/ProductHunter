from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import settings 

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_price_drop_email_async(to_email: str, product_name: str, current_price: float, target_price: float):
    html_content = f"""
    <div style="font-family: Arial, sans-serif;">
        <h2 style="color: #FF5722;">🔥 Thông báo giảm giá!</h2>
        <p>Sản phẩm <strong>{product_name}</strong> đã giảm giá.</p>
        <p>💵 Giá hiện tại: <strong style="color: green;">{current_price:,.0f} VNĐ</strong></p>
        <p>🎯 Ngưỡng của bạn: {target_price:,.0f} VNĐ</p>
    </div>
    """

    message = MessageSchema(
        subject=f"🔥 Giá giảm: {product_name}",
        recipients=[to_email],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_password_reset_email_async(to_email: str, reset_link: str):
    html_content = f"""
    <div style="font-family: Arial, sans-serif;">
        <h2 style="color: #2563EB;">Reset mật khẩu ProductHunter</h2>
        <p>Bạn vừa yêu cầu đặt lại mật khẩu.</p>
        <p>Nhấn vào liên kết bên dưới để tiếp tục:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>Nếu không phải bạn yêu cầu, hãy bỏ qua email này.</p>
    </div>
    """

    message = MessageSchema(
        subject="Đặt lại mật khẩu ProductHunter",
        recipients=[to_email],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
