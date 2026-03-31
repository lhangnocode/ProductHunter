import pandas as pd
import time
import urllib.parse
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth
from bs4 import BeautifulSoup
from datetime import datetime
import sys

class FptTrojanPro:
    def __init__(self):
        self.all_results = []
        self.base_url = 'https://fptshop.com.vn'
        
        # Danh sách toàn bộ danh mục FPT Shop (Đã chuyển sang dạng Slug chuẩn)
        self.categories = [
            # --- ĐỒ ĐIỆN TỬ & CÔNG NGHỆ ---
            "dien-thoai", "may-tinh-xach-tay", "may-tinh-bang", "dong-ho-thong-minh",
            "may-tinh-de-ban", "man-hinh", "linh-kien-may-tinh", "phu-kien",
            "may-in", "phan-mem", "thiet-bi-mang", "smart-home",
            
            # --- ĐIỆN TỬ - ĐIỆN LẠNH ---
            "tivi", "dieu-hoa", "tu-lanh", "tu-dong", "may-giat", "may-say-quan-ao",
            
            # --- GIA DỤNG & SỨC KHỎE ---
            "robot-hut-bui", "may-hut-bui", "may-loc-khong-khi", "may-hut-am",
            "quat", "may-loc-nuoc", "cay-nuoc-nong-lanh", "may-massage", "may-say-toc",
            
            # --- THIẾT BỊ NHÀ BẾP ---
            "noi-chien-khong-dau", "lo-vi-song", "lo-nuong", "bep-nuong-dien",
            "may-rua-bat", "may-hut-mui", "noi-com-dien", "am-sieu-toc",
            "may-xay-sinh-to", "bep-dien-tu", "noi-ap-suat"
        ]

    def scroll_and_load_all(self, page):
        """Hàm xử lý Tắt Popup, Cuộn và Click nút Xem thêm bằng Smart Wait"""
        
        # 1. Rà soát và tắt Popup Cookie/Quảng cáo
        try:
            print("[*] Đang rà soát và tắt Popup Cookie/Quảng cáo...")
            cookie_btn = page.locator("text='Chấp nhận'")
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass 

        click_count = 0
        stuck_counter = 0 # Bộ đếm chống kẹt
        
        # 2. Vòng lặp tải dữ liệu
        while True:
            # Cuộn xuống gần cuối trang để kích nút Xem thêm
            page.evaluate("window.scrollTo(0, document.body.scrollHeight - 800);")
            page.wait_for_timeout(1500)

            # Lấy số lượng sản phẩm TRƯỚC KHI bấm
            count_before = page.locator("div[class*='cardDefault']").count()

            try:
                # Tiêm JS để quét và bấm nút Xem thêm (Quét ngược từ dưới lên để lấy nút chính xác nhất)
                clicked = page.evaluate("""
                    () => {
                        let btns = Array.from(document.querySelectorAll('button'));
                        let loadMoreBtn = btns.reverse().find(b => b.innerText.includes('Xem thêm') || b.textContent.includes('Xem thêm'));
                        if (loadMoreBtn) {
                            loadMoreBtn.click();
                            return true;
                        }
                        return false;
                    }
                """)
                
                if not clicked:
                    print(f"[*] Không tìm thấy nút 'Xem thêm' nữa. Đã đến đáy danh mục!")
                    break
                    
                print(f"[*] Đã bấm 'Xem thêm' lần {click_count + 1} (Đang có {count_before} SP). Chờ server trả hàng...")
                
                try:
                    # SMART WAIT: Bắt trình duyệt đợi tới khi số lượng SP > count_before (Tối đa 15s)
                    page.wait_for_function(
                        f"document.querySelectorAll('div[class*=\"cardDefault\"]').length > {count_before}", 
                        timeout=15000
                    )
                    click_count += 1
                    stuck_counter = 0 # Nếu thành công, reset bộ đếm kẹt
                    
                except Exception:
                    # Nếu đợi 15s mà số lượng không tăng, nghi ngờ là Nút Zombie
                    stuck_counter += 1
                    if stuck_counter >= 5:
                        print(f"\n[!] PHÁT HIỆN NÚT ZOMBIE: Đã thử 5 lần (chờ tổng cộng ~75s) nhưng web ngừng nhả dữ liệu. Rút lui với {count_before} SP!")
                        break
                    else:
                        print(f"[*] Cảnh báo kẹt mạng ({stuck_counter}/5): Web phản hồi chậm, sẽ thử click ép lại...")
                
            except Exception as e:
                print(f"[*] Lỗi tương tác không xác định: {e}. Dừng tải.")
                break

        # 3. Cuộn chậm để tải toàn bộ ảnh (Lazy Load)
        print(f"[*] Hoàn tất mở rộng trang. Đang cuộn lấy ảnh sắc nét...")
        page.evaluate("window.scrollTo(0, 0);")
        
        # Tính toán số lần cuộn dựa trên số SP thực tế để không bị sót ảnh
        total_items = page.locator("div[class*='cardDefault']").count()
        scroll_steps = int(total_items / 8) + 3
        
        for _ in range(scroll_steps):
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(300) 
        page.wait_for_timeout(2000)

    def extract_brand(self, name):
        """Đoán hãng sản xuất từ tên sản phẩm để chia cột cho đẹp"""
        if not name: return "FPT Shop"
        words = name.split()
        brand = words[0].capitalize()
        
        # Lọc bỏ các danh từ chung chung đứng ở đầu tên
        if brand.lower() in ["điện", "máy", "laptop", "pc", "màn", "tủ", "lò", "nồi", "bếp", "quạt", "robot", "loa"]:
            if len(words) >= 3:
                brand = words[2].capitalize() if brand.lower() in ["điện", "máy"] else words[1].capitalize()
        return brand

    def parse_product_block(self, block, category):
        """Bóc tách thông tin chuẩn từ khối HTML"""
        # Lấy Tên & Link
        name_tag = block.find('h3', class_=lambda c: c and 'cardTitle' in c)
        if not name_tag or not name_tag.find('a'): return None
        
        name = name_tag.find('a').get('title', '').strip() or name_tag.text.strip()
        if len(name) < 5: return None
        
        link_tag = name_tag.find('a', href=True)
        slug = urllib.parse.urljoin(self.base_url, link_tag['href']) if link_tag else "N/A"

        # Lấy Giá
        price_container = block.find('div', class_=lambda c: c and 'cardInfo' in c)
        price = 'Liên hệ'
        if price_container:
            price_tag = price_container.find('p', class_=lambda c: c and 'b1-semibold' in c)
            if price_tag:
                 price = price_tag.text.strip()
            else:
                 price_tags = price_container.find_all(string=lambda text: text and ('₫' in text or 'đ' in text.lower()))
                 if price_tags: price = price_tags[0].strip()

        # Lấy Ảnh
        img_container = block.find('div', class_=lambda c: c and 'relative' in c)
        img_url = "N/A"
        if img_container:
            img_tag = img_container.find('img')
            if img_tag:
                srcset = img_tag.get('srcset')
                img_url = srcset.split(',')[0].split(' ')[0].strip() if srcset else img_tag.get('src', 'N/A')

        brand = self.extract_brand(name)

        return {
            'Tên Sản Phẩm': name,
            'Giá': price,
            'Slug (Link)': slug,
            'Main Image URL': img_url,
            'Category': category,
            'Brand / Shop': brand
        }

    def crawl(self):
        start_time = datetime.now()
        print(f"\n[+] KHỞI ĐỘNG CHIẾN DỊCH CÀO TOÀN BỘ FPT SHOP - {start_time}")
        
        with sync_playwright() as p:
            # Mở trình duyệt có giao diện để dễ theo dõi
            browser = p.chromium.launch(headless=False) 
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            for category in self.categories:
                # KỸ THUẬT TIẾT KIỆM RAM: Mở Tab mới cho mỗi danh mục, xài xong đóng lại
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                
                url = f"{self.base_url}/{category}"
                print(f"\n{'='*60}\n>>> MỤC TIÊU MỚI: {url}\n{'='*60}")

                try:
                    page.goto(url, timeout=90000)
                    
                    if "cloudflare" in page.title().lower() or "just a moment" in page.title().lower():
                        print("[!] Chốt chặn Cloudflare! Hãy click xác nhận trên trình duyệt...")
                        page.wait_for_selector("h3", timeout=120000) 
                        print("[+] Đã qua mặt Cloudflare!")

                    # Thực thi chuỗi thao tác tự động
                    self.scroll_and_load_all(page)

                    soup = BeautifulSoup(page.content(), 'html.parser')
                    product_blocks = soup.find_all('div', class_=lambda c: c and 'cardDefault' in c)
                    
                    parsed_items = []
                    for block in product_blocks:
                        item_data = self.parse_product_block(block, category)
                        if item_data:
                            parsed_items.append(item_data)
                        
                    print(f"[+] Bóc tách thành công {len(parsed_items)} sản phẩm ngành {category}.")
                    
                    # Cộng dồn dữ liệu và LƯU FILE NGAY LẬP TỨC để phòng ngừa sự cố
                    self.all_results.extend(parsed_items)
                    self.clean_and_save() 

                except Exception as e:
                    print(f"[-] Bỏ qua danh mục {category} do gặp lỗi: {e}")
                
                finally:
                    # Rất quan trọng: Đóng Tab sau khi cào xong để giải phóng RAM
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
        
        # Màng lọc thép: Tìm kiếm và chém mọi SP trùng đường link
        initial_count = len(df)
        df = df.drop_duplicates(subset=['Slug (Link)'], keep='first')
        df = df.dropna(subset=['Slug (Link)']) 
        final_count = len(df)
        
        filename = 'fpt_full_data.csv'
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f" [LƯU TRỮ AN TOÀN] Đã cập nhật file {filename} | Đang có tổng: {final_count} sản phẩm.")

if __name__ == "__main__":
    try:
        crawler = FptTrojanPro()
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n[!] Bạn đã nhấn Ctrl+C. Hệ thống dừng khẩn cấp!")
        sys.exit(0)