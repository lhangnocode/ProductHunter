class StorageManager:
    def __init__(self, db_manager, typesense_manager):
        self.db_manager = db_manager
        self.typesense_manager = typesense_manager
        
    def upsert_product(self, product_id: str, raw_name: str, slug: str) -> None:
        pass
    
    def upsert_platform_product(self, platform: str, platform_product_id: str, product_id: str) -> None:
        pass