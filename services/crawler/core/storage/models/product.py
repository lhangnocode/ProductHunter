class Product:
    def __init__(self, normalized_name: str, slug: str, brand: str = None, category: str = None, main_image_url: str = None):
        self.normalized_name = normalized_name
        self.slug = slug
        self.brand = brand
        self.category = category
        self.main_image_url = main_image_url
    
    def to_dict(self) -> dict:
        return {
            "normalized_name": self.normalized_name,
            "slug": self.slug,
            "brand": self.brand,
            "category": self.category,
            "main_image_url": self.main_image_url
        }