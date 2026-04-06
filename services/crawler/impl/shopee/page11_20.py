from playwright.sync_api import sync_playwright
import time
import random
import csv # Thư viện lưu file Excel/CSV
import re

def generate_shopee_url(name, shopid, itemid):
    """Tạo URL sản phẩm chuẩn của Shopee"""
    # Xóa ký tự đặc biệt để tạo slug
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name).strip().replace(' ', '-')
    # Giới hạn độ dài slug để URL không quá dài
    slug = slug[:120] 
    return f"https://shopee.vn/{slug}-i.{shopid}.{itemid}"

def run(playwright):
    print("🚀 Đang kết nối với Chrome thật qua CDP (Cổng 9222)...")
    try:
        browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
    except Exception as e:
        print("❌ Không thể kết nối. Hãy chắc chắn Chrome đang bật với cổng 9222.")
        return

    context = browser.contexts[0]
    page = context.new_page()

    scraped_products = [] # Danh sách lưu trữ toàn bộ data

    def handle_response(response):
        if "api/v4/search/search_items" in response.url and response.status == 200:
            try:
                data = response.json()
                items = data.get('items', [])
                for item in items:
                    basic = item.get('item_basic', {})
                    
                    # 1. Tên đầy đủ
                    full_name = basic.get('name', 'Unknown')
                    
                    # 2. Giá cả (Cần chia cho 100,000 theo chuẩn Shopee)
                    raw_price = basic.get('price')
                    price = int(raw_price / 100000) if raw_price else 0
                    
                    # 3. ID Shop và ID Sản phẩm
                    shopid = basic.get('shopid', '')
                    itemid = basic.get('itemid', '')
                    
                    # 4. Tên Shop (Có thể nằm trong block 'shop_info')
                    # Lưu ý: Đôi khi API search không trả thẳng shop_name, ta dùng shopid làm gốc
                    shop_info = item.get('shop_info', {})
                    shop_name = shop_info.get('shop_name', f"Shop_ID_{shopid}")
                    
                    # 5. Đã bán (historical_sold)
                    sold_count = basic.get('historical_sold', 0)

                    # 6. Tạo URL
                    product_url = generate_shopee_url(full_name, shopid, itemid)

                    product_data = {
                        "Tên Sản Phẩm": full_name,
                        "Giá (VNĐ)": price,
                        "Đã Bán": sold_count,
                        "Tên Shop": shop_name,
                        "Shop ID": shopid,
                        "Link Sản Phẩm": product_url
                    }
                    
                    scraped_products.append(product_data)
                    print(f"[{len(scraped_products)}] 👉 {full_name[:40]}... | {price:,} đ | Đã bán: {sold_count}")
                    
            except Exception as e:
                pass

    page.on("response", handle_response)

    # base_url = "https://shopee.vn/search?keyword=laptop"
    # print(f"👉 Điểu hướng tới trang đầu tiên: {base_url}")
    # page.goto(base_url)
    # time.sleep(8) 

    # --- ĐIỀU CHỈNH SỐ TRANG MUỐN CÀO Ở ĐÂY ---
    # MAX_PAGES = 10 # Cào 10 trang = 600 sản phẩm
    
    # for current_page in range(1, MAX_PAGES + 1):
    #     print(f"\n" + "="*50)
    #     print(f"📖 ĐANG QUÉT TRANG SỐ {current_page}")
    #     print("="*50)

    START_PAGE = 11 # Trang bắt đầu (Người dùng nhìn thấy)
    END_PAGE = 20   # Trang kết thúc (Người dùng nhìn thấy)
    
    # URL ban đầu cho trang 11
    page_param = START_PAGE - 1
    base_url = f"https://shopee.vn/search?keyword=laptop&page={page_param}"
    print(f"👉 Điểu hướng tới trang bắt đầu mới: {base_url}")
    page.goto(base_url)
    time.sleep(10) 

    for current_page in range(START_PAGE, END_PAGE + 1):
        print(f"\n" + "="*50)
        print(f"📖 ĐANG QUÉT TRANG SỐ {current_page}")
        print("="*50)

        print("⬇️ Bắt đầu cuộn trang...")
        for _ in range(6): 
            page.evaluate("window.scrollBy(0, 1500);")
            time.sleep(random.uniform(2.5, 5.0))

        if current_page < END_PAGE:
            next_page_param = f"page={current_page}" 
            try:
                next_btn = page.locator(f"a[href*='{next_page_param}']").first
                if next_btn.is_visible():
                    next_btn.scroll_into_view_if_needed()
                    time.sleep(random.uniform(1.0, 2.5))
                    next_btn.click()
                    print(f"✅ Đã chuyển sang trang {current_page + 1}")
                    time.sleep(random.uniform(5.0, 8.0))
                else:
                    break
            except Exception:
                break

    print(f"\n🎉 THU THẬP HOÀN TẤT: Lấy được {len(scraped_products)} sản phẩm.")
    page.close()

    # --- LƯU RA FILE CSV (MỞ BẰNG EXCEL) ---
    if scraped_products:
        filename = "shopee_laptop_data.csv"
        print(f"💾 Đang lưu dữ liệu ra file: {filename}...")
        
        # Lấy tiêu đề cột từ dictionary đầu tiên
        keys = scraped_products[0].keys()
        
        # Ghi file với mã hóa utf-8-sig để Excel đọc không bị lỗi font tiếng Việt
        with open(filename, 'w', newline='', encoding='utf-8-sig') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(scraped_products)
            
        print("✅ Đã lưu file thành công!")

with sync_playwright() as p:
    run(p)