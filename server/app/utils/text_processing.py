import re

# 1. Tập hợp các từ khóa rác thường gặp trên Shopee/Lazada (Nên lưu trong DB để dễ cập nhật)
SPAM_WORDS = {
    "freeship", "freeship extra", "chính hãng", "bảo hành", "giá hủy diệt", 
    "rẻ vô địch", "flash sale", "hàng qt", "quốc tế", "tặng kèm", 
    "nguyên seal", "chống ồn", "new 100%", "hot", "xả kho", "hỏa tốc"
}

def normalize_product_name(raw_name: str) -> str:
    if not raw_name:
        return ""

    # Bước 1: Chuyển thành chữ thường
    name = raw_name.lower()

    # Bước 2: Xóa các cụm nằm trong ngoặc vuông [], ngoặc tròn (), ngoặc nhọn {}
    # Ví dụ: "[Mã giảm 50k] Tai nghe Sony" -> " Tai nghe Sony"
    name = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}', ' ', name)

    # Bước 3: Xóa các ký tự đặc biệt, emoji, dấu gạch ngang (chỉ giữ lại chữ, số và dấu cách)
    # Lưu ý: Giữ lại dấu gạch ngang '-' ở giữa các từ vì mã sản phẩm hay dùng (VD: WH-1000XM5)
    name = re.sub(r'[^\w\s-]', ' ', name)

    # Bước 4: Xóa từ khóa rác (Spam words)
    # Tách chuỗi thành mảng các từ, ghép lại thành các cụm để so sánh (hoặc duyệt qua tập SPAM_WORDS)
    for spam_word in SPAM_WORDS:
        # Cần \b để đảm bảo xóa đúng từ (word boundary), không xóa nhầm cụm từ chứa nó
        # Ví dụ: không xóa chữ "hot" trong từ "hotdog"
        pattern = r'\b' + re.escape(spam_word) + r'\b'
        name = re.sub(pattern, ' ', name)

    # Bước 5: Xóa khoảng trắng thừa và chuẩn hóa lại
    name = ' '.join(name.split())
    
    return name

# --- Test thử nghiệm ---
if __name__ == "__main__":
    raw_text = "[Freeship Extra] Tai nghe chụp tai Sony WH-1000XM5 chống ồn chủ động - Hàng Chính Hãng (Bảo hành 12 tháng) 🔥"
    clean_text = normalize_product_name(raw_text)
    
    print(f"Gốc: {raw_text}")
    print(f"Chuẩn hóa: {clean_text}")
