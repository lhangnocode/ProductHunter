from playwright.sync_api import sync_playwright
import time
import random
import csv
import re
import os # Thêm thư viện os để kiểm tra file tồn tại

def generate_shopee_url(name, shopid, itemid):
    """Tạo URL sản phẩm chuẩn của Shopee"""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name).strip().replace(' ', '-')
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

    # --- BƯỚC 1: ĐỌC DỮ LIỆU CŨ ĐỂ KIỂM TRA TRÙNG LẶP ---
    existing_urls = set() # Sử dụng Set để tra cứu siêu nhanh (O(1))
    filename = "shopee_laptop_data.csv"
    
    if os.path.exists(filename):
        print(f"📂 Tìm thấy file '{filename}'. Đang nạp dữ liệu cũ...")
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Lấy link sản phẩm đã lưu đưa vào bộ nhớ
                url = row.get("Link Sản Phẩm")
                if url:
                    existing_urls.add(url)
        print(f"📦 Đã tải {len(existing_urls)} sản phẩm từ lịch sử để đối chiếu.")
    else:
        print("⚠️ Chưa có file dữ liệu cũ, sẽ cào từ đầu.")

    scraped_products = [] 
    total_skipped = 0 # Biến đếm số sản phẩm bị bỏ qua do trùng

    def handle_response(response):
        nonlocal total_skipped
        if "api/v4/search/search_items" in response.url and response.status == 200:
            try:
                data = response.json()
                items = data.get('items', [])
                for item in items:
                    basic = item.get('item_basic', {})
                    
                    full_name = basic.get('name', 'Unknown')
                    raw_price = basic.get('price')
                    price = int(raw_price / 100000) if raw_price else 0
                    shopid = basic.get('shopid', '')
                    itemid = basic.get('itemid', '')
                    shop_info = item.get('shop_info', {})
                    shop_name = shop_info.get('shop_name', f"Shop_ID_{shopid}")
                    sold_count = basic.get('historical_sold', 0)

                    product_url = generate_shopee_url(full_name, shopid, itemid)

                    # --- BƯỚC 2: KIỂM TRA TRÙNG LẶP ---
                    if product_url in existing_urls:
                        total_skipped += 1
                        continue # Bỏ qua, không làm gì thêm với sản phẩm này

                    # Nếu là sản phẩm mới, thêm vào danh sách và cập nhật bộ nhớ
                    existing_urls.add(product_url)
                    
                    product_data = {
                        "Tên Sản Phẩm": full_name,
                        "Giá (VNĐ)": price,
                        "Đã Bán": sold_count,
                        "Tên Shop": shop_name,
                        "Shop ID": shopid,
                        "Link Sản Phẩm": product_url
                    }
                    
                    scraped_products.append(product_data)
                    print(f"[Mới: {len(scraped_products)}] 👉 {full_name[:40]}... | {price:,} đ")
                    
            except Exception as e:
                pass

    page.on("response", handle_response)

    # --- BƯỚC 3: CÀO TIẾP TỪ TRANG 11 ĐẾN 20 ---
    START_PAGE = 11
    END_PAGE = 20
    
    # URL ban đầu cho trang 11 (Shopee đếm page từ 0 nên trang 11 là page=10)
    base_url = f"https://shopee.vn/search?keyword=laptop&page={START_PAGE - 1}"
    print(f"\n👉 Điểu hướng tới trang bắt đầu: {base_url}")
    page.goto(base_url)
    time.sleep(8) 
    
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

    print(f"\n🎉 THU THẬP HOÀN TẤT!")
    print(f"   - Sản phẩm mới lấy được: {len(scraped_products)}")
    print(f"   - Sản phẩm bỏ qua do trùng: {total_skipped}")
    page.close()

    # --- BƯỚC 4: GHI NỐI TIẾP VÀO FILE CSV ---
    if scraped_products:
        print(f"💾 Đang lưu dữ liệu mới vào file: {filename}...")
        
        keys = scraped_products[0].keys()
        file_exists = os.path.isfile(filename)
        
        # Mở file với chế độ 'a' (append) để ghi nối tiếp xuống cuối file
        with open(filename, 'a', newline='', encoding='utf-8-sig') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            # Chỉ ghi lại Header (tiêu đề cột) nếu file chưa từng tồn tại
            if not file_exists:
                dict_writer.writeheader()
            dict_writer.writerows(scraped_products)
            
        print("✅ Đã cập nhật file thành công!")

with sync_playwright() as p:
    run(p)