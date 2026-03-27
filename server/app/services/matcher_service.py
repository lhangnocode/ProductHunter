import logging

from requests import Session
from app.db.session import AsyncSessionLocal
from app.utils.text_processing import normalize_product_name
from app.core.lifespan import ai_model 
from app.db.typesense_client import ts_client 
from sqlalchemy import update  
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
from app.models.platform_product import PlatformProduct 

logger = logging.getLogger(__name__)

async def process_and_match_product(platform_product_id: int, raw_name: str, db: Session):
    """
    Hàm xử lý ngầm (Background Task):
    Nhận 1 sản phẩm từ crawler -> Clean text -> Vectorize -> Typesense Search -> Update DB
    """
    logger.info(f"Bắt đầu xử lý sản phẩm ID: {platform_product_id} - {raw_name}")
    # // Clean text
    clean_name = normalize_product_name(raw_name)
    if not clean_name:
        logger.warning(f"Sản phẩm ID {platform_product_id} có tên rỗng sau khi clean.")
        return
    
    # Vector by model AI
    try:
        vector_embedding = ai_model["sbert"].encode(clean_name).tolist()
    except Exception as e:
        logger.error(f"Lỗi khi chạy model AI cho ID {platform_product_id}: {e}")
        return
    
    # Search TYPESENSE
    try:
        vector_str = ",".join(map(str, vector_embedding))
        
        search_result = ts_client.collections['products'].documents.search({
            'q': '*', 
            'vector_query': f'vector_field:([{vector_str}], k:1)'
        })
        
        hits = search_result.get('hits', [])
        
    except Exception as e:
        logger.error(f"Lỗi gọi Typesense API: {e}")
        return

    # SQL TRANSACTIONS
    async with AsyncSessionLocal() as db_session:
        try:
            if hits and hits[0]['vector_distance'] <= 0.2:
                # Đã có Master Product -> Chỉ Update
                master_id = int(hits[0]['document']['id'])
                
                stmt = update(PlatformProduct).where(
                    PlatformProduct.id == platform_product_id
                ).values(product_id=master_id, status="matched")
                
                await db_session.execute(stmt)
                await db_session.commit()
                
            else:
                # Chưa có Master Product -> Tạo mới -> Gọi Typesense Create -> Update
                # Lưu ý cú pháp Async
                new_master = Product(name=clean_name)
                db_session.add(new_master)
                await db_session.flush() # Lấy ID mới
                
                # Gọi sync HTTP tới Typesense để insert
                # ... ts_client.collections.create(...)
                
                # Cập nhật PlatformProduct
                stmt = update(PlatformProduct).where(
                    PlatformProduct.id == platform_product_id
                ).values(product_id=new_master.id, status="created")
                
                await db_session.execute(stmt)
                await db_session.commit()
                
        except Exception as e:
            await db_session.rollback()
            logger.error(f"Lỗi DB trong Background Task: {e}")