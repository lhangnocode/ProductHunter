import pandas as pd
import time
import urllib.parse
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth
from bs4 import BeautifulSoup
from datetime import datetime
import sys

class PhongVuCrawler:
    def __init__(self):
        self.all_results = []
        self.base_url = 'https://phongvu.vn'
        
        # Danh mục chuẩn của Phong Vũ (Slug)
        self.categories = [
            "c/laptop", "c/apple", "c/dien-may", "c/dien-gia-dung",
            "c/pc", "c/man-hinh-may-tinh", "c/linh-kien-may-tinh",
            "c/phu-kien", "c/gaming-gear", "c/dien-thoai-tablet",
            "c/thiet-bi-am-thanh", "c/thiet-bi-van-phong"
        ]

    def extract_brand(self, name):
        """Đoán hãng sản xuất từ tên sản phẩm"""
        if not name: return "Phong Vũ"
        words = name.split()
        brand = words[0].capitalize()
        
        if brand.lower() in ["laptop", "pc", "màn", "chuột", "bàn", "tai", "loa", "tivi", "máy", "điện", "apple", "vỏ", "nguồn", "ổ", "ram", "card", "cpu", "mainboard"]:
            if len(words) >= 3:
                brand = words[2].capitalize() if brand.lower() in ["máy", "điện", "ổ", "card", "màn", "tai"] else words[1].capitalize()
        return brand

    def scroll_and_load_all(self, page):
        """Hàm tự động cuộn và đấm nút 'Xem thêm sản phẩm' liên tục"""
        
        # 1. Tắt Popup quảng cáo nếu có
        try:
            print("[*] Đang rà soát và tắt Popup...")
            page.mouse.click(10, 10) # Click ra rìa màn hình để tắt popup
            page.wait_for_timeout(1000)
        except Exception:
            pass 

        click_count = 0
        stuck_counter = 0 
        
        while True:
            # Cuộn xuống gần cuối để nút Xem thêm hiện ra
            page.evaluate("window.scrollTo(0, document.body.scrollHeight - 800);")
            page.wait_for_timeout(1500)

            # Lấy số lượng sản phẩm hiện tại bằng cách đếm ký hiệu '₫' (Mỏ neo)
            count_before = page.locator("text='₫'").count()

            try:
                # Tiêm JS để nhắm trúng nút có chữ "Xem thêm sản phẩm"
                clicked = page.evaluate("""
                    () => {
                        let elements = Array.from(document.querySelectorAll('button, div, a, span'));
                        let loadMoreBtn = elements.reverse().find(b => 
                            b.innerText && 
                            (b.innerText.toLowerCase().includes('xem thêm sản phẩm') || b.innerText.toLowerCase().includes('xem thêm')) && 
                            b.innerText.length < 40
                        );
                        if (loadMoreBtn) {
                            loadMoreBtn.click();
                            return true;
                        }
                        return false;
                    }
                """)
                
                if not clicked:
                    print(f"[*] Không tìm thấy nút 'Xem thêm sản phẩm'. Đã cào đến đáy danh mục!")
                    break
                    
                print(f"[*] Đã bấm 'Xem thêm sản phẩm' lần {click_count + 1} (Đang có {count_before} SP). Chờ tải...")
                
                # --- SMART WAIT: Đợi cho đến khi số lượng chữ '₫' tăng lên ---
                is_loaded = False
                for _ in range(15): # Chờ tối đa 15 giây (15 lần x 1000ms)
                    page.wait_for_timeout(1000)
                    if page.locator("text='₫'").count() > count_before:
                        is_loaded = True
                        break
                
                if is_loaded:
                    click_count += 1
                    stuck_counter = 0 # Thành công thì reset biến kẹt
                else:
                    stuck_counter += 1
                    if stuck_counter >= 5: # Cho phép kẹt mạng 5 lần
                        print(f"\n[!] PHÁT HIỆN NÚT ZOMBIE: Thử 5 lần nhưng web ngừng nhả dữ liệu. Rút lui với {count_before} SP!")
                        break
                    else:
                        print(f"[*] Cảnh báo kẹt ({stuck_counter}/5): Mạng chậm, sẽ cuộn và thử click lại...")
                
            except Exception as e:
                print(f"[*] Lỗi tương tác nút: {e}. Dừng tải.")
                break

        # Cuộn dọc từ trên xuống để ép tải toàn bộ ảnh gốc (Lazy load)
        print(f"[*] Hoàn tất bung HTML. Đang cuộn rà soát để tải ảnh sắc nét...")
        page.evaluate("window.scrollTo(0, 0);")
        total_items = page.locator("text='₫'").count()
        
        # Công thức: 1 lần cuộn được khoảng 10 sản phẩm
        scroll_steps = int(total_items / 10) + 3
        for _ in range(scroll_steps):
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(300) 
        page.wait_for_timeout(2000)

    def parse_product_block(self, p_tag, category, seen_links):
        """Thuật toán mỏ neo: Leo ngược từ chữ '₫' lên thẻ bọc ngoài để lấy thông tin"""
        parent = p_tag.parent
        for _ in range(6): # Leo tối đa 6 cấp HTML
            if not parent: break
            
            link_tag = parent.find('a', href=True)
            img_tag = parent.find('img')
            
            # Đã tìm thấy điểm hội tụ của Link và Ảnh
            if link_tag and img_tag:
                href = link_tag['href']
                slug = urllib.parse.urljoin(self.base_url, href)
                
                # Bỏ qua các link rác hệ thống (Chống nhiễu)
                if any(bad in slug for bad in ['help.', '/p/he-thong']):
                    return None
                    
                if slug in seen_links:
                    return None
                    
                seen_links.add(slug)
                
                # Bóc Tên
                name_tag = parent.find(['h3', 'div'], class_=lambda c: c and ('product-name' in c.lower() or 'title' in c.lower()))
                name = name_tag.text.strip() if name_tag else link_tag.text.strip()
                if len(name) < 5: return None 
                
                # Bóc Giá (Chính là thẻ cha của chữ ₫)
                price = p_tag.parent.text.strip()
                
                # Bóc Ảnh
                img_url = img_tag.get('src') or img_tag.get('data-src', 'N/A')
                brand = self.extract_brand(name)

                return {
                    'Tên Sản Phẩm': name,
                    'Giá': price,
                    'Slug (Link)': slug,
                    'Main Image URL': img_url,
                    'Category': category.replace('c/', ''),
                    'Brand / Shop': brand
                }
            parent = parent.parent
        return None

    def crawl(self):
        start_time = datetime.now()
        print(f"\n[+] KHỞI ĐỘNG CỖ MÁY CÀO PHONG VŨ - {start_time}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False) 
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            for category in self.categories:
                # Đóng/Mở Tab để tránh tràn RAM
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                
                url = f"{self.base_url}/{category}"
                print(f"\n{'='*60}\n>>> MỤC TIÊU MỚI: {url}\n{'='*60}")

                try:
                    page.goto(url, timeout=90000, wait_until="domcontentloaded")
                    
                    # 1. Gọi hàm tự động click "Xem thêm sản phẩm"
                    self.scroll_and_load_all(page)

                    # 2. Đẩy vào BeautifulSoup bóc tách dựa trên mỏ neo ₫
                    soup = BeautifulSoup(page.content(), 'html.parser')
                    price_tags = soup.find_all(string=lambda text: text and '₫' in text)
                    
                    parsed_items = []
                    seen_links = set()
                    
                    for p_tag in price_tags:
                        item_data = self.parse_product_block(p_tag, category, seen_links)
                        if item_data:
                            parsed_items.append(item_data)
                            
                    print(f"[+] Bóc tách thành công {len(parsed_items)} sản phẩm ngành {category}.")
                    
                    # 3. Lưu luôn và ngay vào ổ cứng (Tránh mất data nếu cúp điện)
                    self.all_results.extend(parsed_items)
                    self.clean_and_save() 

                except Exception as e:
                    print(f"[-] Bỏ qua danh mục {category} do gặp lỗi: {e}")
                
                finally:
                    page.close()
                    time.sleep(2)
                        
            browser.close()
            
            end_time = datetime.now()
            print("\n" + "#"*60)
            print(f"[+] CHIẾN DỊCH HOÀN TẤT! TỔNG THỜI GIAN: {end_time - start_time}")
            print("#"*60 + "\n")

    def clean_and_save(self):
        if not self.all_results:
            return

        df = pd.DataFrame(self.all_results)
        
        # Xóa trùng lặp bằng Pandas
        initial_count = len(df)
        df = df.drop_duplicates(subset=['Slug (Link)'], keep='first')
        df = df.dropna(subset=['Slug (Link)']) 
        final_count = len(df)
        
        filename = 'phongvu_full_data.csv'
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"   ↳ [ĐÃ LƯU] File {filename} | Kho đang có: {final_count} món hàng.")

if __name__ == "__main__":
    try:
        crawler = PhongVuCrawler()
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n[!] Nhận lệnh ngắt Ctrl+C. Hệ thống dừng an toàn!")
        sys.exit(0)