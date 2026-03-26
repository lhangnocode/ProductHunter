import csv
import io
import os
import requests
import re
from pathlib import Path

def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / "server" / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()

API_URL = os.getenv("CRAWLER_API_URL", "")
API_KEY = os.getenv("DEV_API_KEY", "")

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Hàm phụ trợ trích xuất slug từ link Shopee
def extract_slug(url):
    match = re.search(r'shopee\.vn/(.*?)-i\.', url)
    return match.group(1) if match else "unknown-slug"

# Hàm phụ trợ nhận diện hãng Laptop từ tên
def guess_brand(name):
    name_lower = name.lower()
    brands = ['dell', 'hp', 'asus', 'lenovo', 'aoc', 'thinkpad', 'acer', 'msi', 'razer', 'gigabyte', 'apple', 'samsung', 'lg']
    for b in brands:
        if b in name_lower:
            return b.capitalize()
    return "Unknown"

def process_and_upload():
    # Sử dụng 'utf-8-sig' để tự động loại bỏ ký tự tàng hình BOM
    filename = "shopee_laptop_data.csv" # Đường dẫn tới file CSV của bạn
    
    print("🚀 Bắt đầu đẩy dữ liệu lên API...\n" + "-"*50)
    
    success_count = 0
    
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Dùng .strip() để đề phòng có dấu cách thừa ở tên cột
                # Cách này an toàn 100% với mọi loại file CSV
                clean_row = {key.strip(): value for key, value in row.items() if key}
                
                name = clean_row["Tên Sản Phẩm"]
                url = clean_row["Link Sản Phẩm"]
                
                payload = {
                    "normalized_name": name,
                    "slug": extract_slug(url),
                    "brand": guess_brand(name),
                    "category": "Laptop",
                    "main_image_url": None
                }
                
                # Gửi request (giữ nguyên như code cũ của bạn)
                response = requests.post(API_URL, json=payload, headers=HEADERS)
                
                if response.status_code in [200, 201]:
                    print(f"✅ Thành công: {name[:40]}...")
                    success_count += 1
                else:
                    print(f"❌ Thất bại ({response.status_code}): {response.text}")
                    
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file '{filename}'. Hãy kiểm tra lại đường dẫn!")
    except Exception as e:
        print(f"⚠️ Đã xảy ra lỗi: {e}")

    print("-" * 50)
    print(f"🎉 Hoàn tất! Đã đẩy thành công {success_count} sản phẩm.")

if __name__ == "__main__":
    process_and_upload()