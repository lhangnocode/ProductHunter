import re
import unicodedata

class ProductNormalizer:
    def __init__(self):
        # Danh sách từ rác thường gặp trên Shopee/Lazada VN
        self.junk_words = [
            r"chính hãng", r"bảo hành", r"freeship", r"miễn phí vận chuyển",
            r"nguyên seal", r"mới 100%", r"like new", r"likenew", r"qua sử dụng",
            r"nhập khẩu", r"quốc tế", r"phiên bản", r"vna", r"vn/a", r"fpt", 
            r"trả góp", r"giảm giá", r"deal", r"flash sale", r"hàng auth", r"cam kết",
            r"đổi trả", r"tháng", r"năm"
        ]
        # Gom danh sách thành 1 chuỗi Regex để chạy cho nhanh
        self.junk_regex = re.compile(r'\b(?:' + '|'.join(self.junk_words) + r')\b', re.IGNORECASE)

    def normalize(self, raw_name: str) -> str:
        if not raw_name:
            return ""

        # 1. Chuẩn hóa Unicode (đưa về chuẩn NFKC)
        text = unicodedata.normalize('NFKC', raw_name)

        # 2. Lowercase
        text = text.lower()

        # 3. Xóa các cụm nằm trong ngoặc: [Mã giảm 5%], (Đen), 【Freeship】
        text = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}|【.*?】', ' ', text)

        # 4. Xóa từ khóa quảng cáo rác (Dùng Regex định nghĩa ở trên)
        text = self.junk_regex.sub(' ', text)

        # 5. Xóa các ký tự đặc biệt (chỉ giữ lại chữ cái, số và khoảng trắng)
        text = re.sub(r'[^\w\s]', ' ', text)

        # 6. CHUẨN HÓA MÃ SẢN PHẨM (Magic step)
        # Mục tiêu: Gom "wh 1000 xm5" hoặc "wh-1000xm5" thành "wh1000xm5"
        # Tìm các cụm có độ dài ngắn (thường là mã) bị cách nhau bởi khoảng trắng
        # Đoạn regex này có thể tùy chỉnh thêm tùy mức độ phức tạp
        
        # Cách đơn giản gọn nhẹ cho đồ Tech: Xóa khoảng trắng giữa Chữ và Số
        text = re.sub(r'(?<=[a-z])\s+(?=[0-9])', '', text) # Nối chữ với số (wh 1000 -> wh1000)
        text = re.sub(r'(?<=[0-9])\s+(?=[a-z])', '', text) # Nối số với chữ (1000 xm5 -> 1000xm5)

        # 7. Dọn dẹp khoảng trắng thừa (Extra spaces)
        text = re.sub(r'\s+', ' ', text).strip()

        return text