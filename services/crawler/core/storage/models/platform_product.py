class PlatformProduct:
    def __init__(self, product_id: str, platform_id: str, raw_name: str, original_item_id: str, url: str, affiliate_url: str, current_price: float, original_price: float, in_stock: bool, last_crawled_at: datetime):
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