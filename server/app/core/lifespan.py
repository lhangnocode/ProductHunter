import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

# Import hàm khởi tạo bảng từ file typesense_client ta vừa viết
from app.db.typesense_client import init_typesense_collections

logger = logging.getLogger(__name__)

# Khởi tạo một Dictionary toàn cục (Global Variable) để chứa Model
# Tất cả các file khác (như matcher_service) sẽ import cái biến này để dùng
ai_model = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hàm này quản lý vòng đời của FastAPI.
    - Code TRƯỚC chữ 'yield' sẽ chạy lúc khởi động server.
    - Code SAU chữ 'yield' sẽ chạy lúc tắt server.
    """
    # ==========================================
    # PHẦN 1: KHỞI ĐỘNG (STARTUP)
    # ==========================================
    logger.info("🚀 Đang khởi động hệ thống Crawler Matcher...")

    # 1. Khởi tạo Typesense
    try:
        init_typesense_collections()
    except Exception as e:
        logger.error(f"❌ Lỗi khi khởi tạo Typesense: {e}")
        # Tùy logic: Bạn có thể raise lỗi để chặn server không cho chạy nếu Typesense sập
        
    # 2. Tải Model AI vào RAM
    logger.info("⏳ Đang tải model AI (Vietnamese SBERT) vào RAM. Sẽ mất vài giây...")
    try:
        # Load model 1 lần duy nhất ở đây
        ai_model["sbert"] = SentenceTransformer('keepitreal/vietnamese-sbert')
        logger.info("✅ Tải model AI thành công! Sẵn sàng xử lý Vector.")
    except Exception as e:
        logger.error(f"❌ Lỗi tải model AI: {e}")

    # ==========================================
    # GIAO QUYỀN CHO FASTAPI CHẠY (NHẬN REQUEST)
    # ==========================================
    yield  

    # ==========================================
    # PHẦN 2: DỌN DẸP KHI TẮT SERVER (SHUTDOWN)
    # ==========================================
    logger.info("🛑 Đang tắt server. Bắt đầu dọn dẹp bộ nhớ...")
    
    # Xóa model khỏi RAM để giải phóng tài nguyên cho hệ điều hành
    ai_model.clear()
    
    logger.info("👋 Đã dọn dẹp xong. Tạm biệt!")