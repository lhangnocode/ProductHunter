from pydantic import BaseModel
from typing import Optional

# 1. Những trường chung mà cả Tạo và Đọc đều có
class PlatformBase(BaseModel):
    name: str
    base_url: str
    affiliate_config: Optional[str] = None

# 2. Dùng khi GỬI dữ liệu lên (Không cần ID vì DB tự sinh)
class PlatformCreate(PlatformBase):
    pass

# 3. Dùng khi TRẢ dữ liệu về (Có thêm ID)
class PlatformResponse(PlatformBase):
    id: int

    class Config:
        from_attributes = True