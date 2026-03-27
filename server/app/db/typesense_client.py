import typesense
import os
import logging

logger = logging.getLogger(__name__)


TYPESENSE_HOST = os.getenv("TYPESENSE_HOST", "localhost")
TYPESENSE_PORT = os.getenv("TYPESENSE_PORT", "8108")
TYPESENSE_PROTOCOL = os.getenv("TYPESENSE_PROTOCOL", "http")
TYPESENSE_API_KEY = os.getenv("TYPESENSE_API_KEY", "your_api_key_here") 

# ==========================================
# 2. KHỞI TẠO CLIENT DUY NHẤT (SINGLETON)
# ==========================================
ts_client = typesense.Client({
    'nodes': [{
        'host': TYPESENSE_HOST,
        'port': TYPESENSE_PORT,
        'protocol': TYPESENSE_PROTOCOL
    }],
    'api_key': TYPESENSE_API_KEY,
    'connection_timeout_seconds': 2
})

# ==========================================
# 3. HÀM KHỞI TẠO BẢNG (COLLECTION SCHEMA)
# ==========================================
def init_typesense_collections():
    """
    Hàm này dùng để tự động tạo bảng 'products' trong Typesense nếu nó chưa tồn tại.
    Bạn có thể gọi hàm này 1 lần duy nhất lúc khởi động server FastAPI (trong file lifespan.py).
    """
    collection_name = 'products'
    
    # Kiểm tra xem bảng đã tồn tại chưa
    try:
        ts_client.collections[collection_name].retrieve()
        logger.info(f"Collection '{collection_name}' đã tồn tại trong Typesense.")
    except typesense.exceptions.ObjectNotFound:
        logger.info(f"Đang tạo mới collection '{collection_name}' trong Typesense...")
        
        # Định nghĩa cấu trúc bảng
        schema = {
            'name': collection_name,
            'fields': [
                # Cột id là bắt buộc, kiểu string
                {'name': 'id', 'type': 'string'}, 
                
                # Cột lưu tên sản phẩm chuẩn hóa
                {'name': 'name', 'type': 'string'}, 
                
                # CỘT QUAN TRỌNG NHẤT: Lưu Vector AI
                {
                    'name': 'vector_field', 
                    'type': 'float[]', 
                    # Model 'keepitreal/vietnamese-sbert' tạo ra vector có 768 chiều
                    'num_dim': 768 
                }
            ]
        }
        
        # Gửi lệnh tạo bảng lên Typesense
        ts_client.collections.create(schema)
        logger.info(f"Tạo collection '{collection_name}' thành công!")

# (Tùy chọn) Chạy thử file này độc lập để test kết nối
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_typesense_collections()