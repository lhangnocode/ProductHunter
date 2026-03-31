class PlatformProduct:
    def __init__(
        self, 
        product_id: str, 
        platform_id: str, 
        raw_name: str, 
        original_item_id: str, 
        url: str, 
        affiliate_url: str, 
        current_price: float, 
        original_price: float, 
        in_stock: bool, 
        last_crawled_at: str,
        rating: float = None,        # Thêm mới (mặc định None)
        reviews_count: int = 0       # Thêm mới (mặc định 0)
    ):
        self.product_id = product_id
        self.platform_id = platform_id
        self.raw_name = raw_name
        self.original_item_id = original_item_id
        self.url = url
        self.affiliate_url = affiliate_url
        self.current_price = current_price
        self.original_price = original_price
        self.in_stock = in_stock
        self.last_crawled_at = last_crawled_at
        self.rating = rating          # Khởi tạo giá trị mới
        self.reviews_count = reviews_count

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "platform_id": self.platform_id,
            "raw_name": self.raw_name,
            "original_item_id": self.original_item_id,
            "url": self.url,
            "affiliate_url": self.affiliate_url,
            "current_price": self.current_price,
            "original_price": self.original_price,
            "in_stock": self.in_stock,
            "last_crawled_at": self.last_crawled_at,
            "rating": self.rating,             # Xuất ra dict để đẩy vào API/DB
            "reviews_count": self.reviews_count
        }