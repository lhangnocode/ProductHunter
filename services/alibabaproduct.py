from curl_cffi import requests
import pandas as pd
import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime
import uuid
from decimal import Decimal
import re
from datetime import datetime, timezone

class AlibabaCaptchaError(Exception):
    pass

class AlibabaCrawler:
    def parse_price_to_decimal(self, price_str):
        """Lấy con số đầu tiên trong chuỗi giá (min price) và chuyển thành Decimal"""
        if not price_str:
            return None
        # Xóa dấu phẩy phân cách hàng nghìn để tránh lỗi parse
        price_str = price_str.replace(',', '')
        # Tìm con số (bao gồm cả phần thập phân)
        match = re.search(r'\d+(\.\d+)?', price_str)
        if match:
            return Decimal(match.group(0))
        return None

    def extract_item_id(self, url):
        """Bóc tách ID gốc của sản phẩm từ URL của Alibaba"""
        if not url:
            return str(uuid.uuid4()) # Fallback nếu không có URL
        match = re.search(r'_(\d+)\.html', url)
        if match:
            return match.group(1)
        # Nếu URL có định dạng khác, tạo một ID giả dựa trên URL để tránh trùng lặp
        return str(uuid.uuid5(uuid.NAMESPACE_URL, url))

    def __init__(self):
        self.all_results = []
        self.base_url = 'https://alibaba.com/trade/search'
        self.session = requests.Session(impersonate="chrome116")
        self.session.cookies.set('intl_locale', 'vi_VN', domain='.alibaba.com')
        self.session.cookies.set('aep_usuc_f', 'region=VN&site=vie&b_locale=vi_VN', domain='.alibaba.com')
        self.categories_list = [
            "điện thoại thông minh", "máy tính xách tay", "máy tính để bàn", "tai nghe bluetooth",
            "camera an ninh", "flycam", "đồng hồ thông minh", "máy chơi game"
         ] 

        self.session.headers.update({
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        })

    def refresh_session_manual(self, category="smartphones"):
        encoded_q = quote(category)
        target_url = f"https://www.alibaba.com/trade/search?SearchText={encoded_q}&page=1"

        print("\n" + "!"*50)
        print(" [!] ALIBABA CHẶN: PHÁT HIỆN CAPTCHA THANH TRƯỢT")
        print(" [!] VUI LÒNG DÙNG CHUỘT KÉO THANH TRƯỢT TRONG TRÌNH DUYỆT")
        print("!"*50 + "\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            stealth = Stealth()
            stealth.apply_stealth_sync(page)

            try:
                page.goto(target_url, timeout=90000, wait_until="commit")
                print(">>> Đang trinh sát trang web (đợi 5 giây)...")
                page.wait_for_timeout(5000)
                
                captcha_slider = "#nc_1_n1z"
                punish_page = "punish"
                
                is_resolved = False
                print(">>> Đang kiểm tra Captcha...")
                
                for _ in range(15):
                    if page.is_visible(captcha_slider) or punish_page in page.url:
                        print("!!! ĐÃ THẤY THANH TRƯỢT CAPTCHA")
                        print(">>> Đang đợi bạn thao tác kéo thanh trượt khớp hình...")
                        
                        try:
                            page.wait_for_selector(captcha_slider, state="hidden", timeout=120000)
                            print("[+] Kéo Captcha THÀNH CÔNG! Đợi trang web tải lại.")
                            page.wait_for_timeout(5000)
                        except:
                            input(">>> Nếu đã xác minh xong thì nhấn phím [ENTER] ở đây")
                            
                    if page.locator('a[href*="//www.alibaba.com/product-detail/"]').count() > 0:
                        print("[+] Đã thấy danh sách sản phẩm thực tế của Alibaba")
                        is_resolved = True
                        break
                        
                    print("... Vẫn đang đợi trang web load sản phẩm ...")
                    page.wait_for_timeout(3000)

                if not is_resolved:
                    print(">>> CẢNH BÁO: Trang web vẫn chưa hiện sản phẩm.")
                    input(">>> HÃY NHẤN F5 TRÊN TRÌNH DUYỆT ĐẾN KHI HIỆN SẢN PHẨM RỒI NHẤN [ENTER] TẠI ĐÂY...")

            except Exception as e:
                print("[-] Quá thời gian chờ hoặc có lỗi xảy ra.")
                raise AlibabaCaptchaError(f"Gạt Captcha thất bại: {e}")

            playwright_cookies = context.cookies()
            new_ua = page.evaluate("navigator.userAgent")
            
            # 1. Xóa sạch cookie cũ bị rác trong session
            self.session.cookies.clear()
            
            # 2. Bốc Cookie chuẩn chỉ: Giữ nguyên Domain và Path
            for cookie in playwright_cookies:
                self.session.cookies.set(
                    cookie['name'], 
                    cookie['value'], 
                    domain=cookie['domain'], 
                    path=cookie['path']
                )

            # 3. Ép lại Cookie Tiếng Việt (Phòng trường hợp Playwright làm mất)
            self.session.cookies.set('intl_locale', 'vi_VN', domain='.alibaba.com', path='/')
            self.session.cookies.set('aep_usuc_f', 'region=VN&site=vie&b_locale=vi_VN', domain='.alibaba.com', path='/')

            # 4. Cập nhật User-Agent và thêm Referer (Rất quan trọng để ngụy trang)
            self.session.headers.update({
                'user-agent': new_ua,
                'referer': 'https://www.alibaba.com/',
                'origin': 'https://www.alibaba.com'
            })
            # --------------------------------------------------
            
            browser.close()
            print("[+] Session đã được làm mới toàn diện. Bắt đầu cào...\n")

    def crawl_page(self, category, page):
        params = {
            'SearchText': category,
            'page': str(page)
        }

        try:
            response = self.session.get(
                self.base_url, 
                params=params,
                timeout=15
            )
        
            if 'punish' in response.url or 'b2b-slide' in response.text or response.status_code == 403:
                print(f"[!] Bị Alibaba chặn ở trang {page} - Đang gọi đội cứu hộ Captcha...")
                self.refresh_session_manual(category)
                return self.crawl_page(category, page)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                products_data = []
                scripts = soup.find_all('script')
                
                for script in scripts:
                    if script.string and '_offer_list' in script.string:
                        text = script.string
                        start = text.find('{')
                        end = text.rfind('}') + 1
                        json_text = text[start:end]
                        
                        try:
                            import json
                            import re
                            data = json.loads(json_text)
                            
                            def find_items(node):
                                if isinstance(node, dict):
                                    if 'title' in node and ('price' in node or 'priceV2' in node):
                                        title = node.get('title') or node.get('subject', '')
                                        title = re.sub(r'<[^>]+>', '', title)
                                        price = node.get('price') or node.get('priceV2', '')
                                        link = node.get('productUrl') or node.get('clickEurl', '')
                                        if link and not link.startswith('http'):
                                            link = 'https:' + link

                                        if title and price:
                                            raw_title = title.strip()
                                            raw_link = link.strip()
                                            raw_price = price.strip()
                                            
                                            item_id = self.extract_item_id(raw_link)
                                            current_price_dec = self.parse_price_to_decimal(raw_price)
                                            
                                            if not any(item['original_item_id'] == item_id for item in products_data):
                                                products_data.append({
                                                    'product_id': None,           
                                                    'platform_id': 1,                     # ID của platform (Gán cứng 1 cho Alibaba, bạn tự đổi theo DB của bạn)
                                                    'raw_name': raw_title,                # Tên gốc lấy về
                                                    'original_item_id': item_id,          # ID sản phẩm trên Alibaba
                                                    'url': raw_link,                      # Link sản phẩm
                                                    'affiliate_url': None,                # Chưa có affiliate
                                                    'current_price': current_price_dec,   # Decimal
                                                    'original_price': None,               # Nếu bóc được giá gốc thì điền vào đây
                                                    'in_stock': True,                     # Mặc định True khi đang hiển thị
                                                    'last_crawled_at': datetime.now(timezone.utc)
                                                })
                                            
                                    for key, value in node.items():
                                        find_items(value)
                                        
                                elif isinstance(node, list):
                                    for item in node:
                                        find_items(item)

                            find_items(data)
                            break
                            
                        except Exception as e:
                            print(f"[!] Lỗi khi giải mã JSON: {e}")

                # --- SỬA LỖI BREAK Ở ĐÂY: Dùng RETURN để trả kết quả về cho hàm chính ---
                if products_data:
                    print(f"[+] Vô mánh! Đã bóc tách thành công {len(products_data)} sản phẩm ở trang {page}.")
                    for p in products_data[:3]:  
                        # Đổi key in ra cho khớp schema mới
                        print(f"    - {p['raw_name'][:50]}... | Giá: {p['current_price']} | ID: {p['original_item_id']}")
                    
                    return products_data
                else:
                    print(f"Cảnh báo: Không parse được sản phẩm ở trang {page} (Có thể do hết trang hoặc lỗi).")
                    return []
            
            else:
                print(f"Lỗi {response.status_code} ở trang {page}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"Lỗi: Timeout ở trang {page}. Mạng yếu hoặc server Alibaba quá tải.")
            return None
        except Exception as e:
            print(f"Có lỗi lạ xảy ra: {str(e)}")
            return None
        
    def crawl_category(self, category, page_start, page_end):
        results_category = []
        print(f"--- Bắt đầu cào dữ liệu từ khóa: {category} ---")
        for page in range(page_start, page_end + 1):
            if page % 10 == 0:
                print("Thời gian hiện tại:", datetime.now())
                time.sleep(random.uniform(30, 60))
                
            data = self.crawl_page(category=category, page=page)
            
            if data:
                results_category.extend(data)
                print(f"Đã xong trang {page}. Các trang đã cào có tổng cộng: {len(results_category)} sản phẩm.")
                time.sleep(random.uniform(5, 12)) 
            else:
                print("Không lấy được dữ liệu nữa, dừng lại chuyển từ khóa")
                break
        return results_category
    
    def crawl_all(self, page_start, page_end):
        try:
            print("Đang khởi tạo Session, lấy Cookie ban đầu...")
            self.refresh_session_manual(self.categories_list[0])

            for category in self.categories_list:
                res_category = self.crawl_category(category, page_start, page_end)
                self.all_results.extend(res_category)
                
            print("\n--- Hoàn thành toàn bộ chiến dịch ---")
        except AlibabaCaptchaError as e:
            print(f"\n[!] DỪNG CÀO: {e}")
        except Exception as e:
            print(f"\n[!] Lỗi không xác định: {e}")
        finally:
            self.save_data_to_csv()
            print("Thời gian kết thúc:", datetime.now())
        
    def save_data_to_csv(self, path_csv="alibaba_products.csv"):
        if self.all_results:
            df = pd.DataFrame(self.all_results)
            df.to_csv(path_csv, index=False, encoding="utf-8-sig")
            print(f"Đã lưu thành công {len(self.all_results)} sản phẩm vào file {path_csv}")
        else:
            print("Không có dữ liệu nào để lưu.")

if __name__ == "__main__":
    start_time = datetime.now()
    print("Thời gian bắt đầu:", start_time)
    
    crawl_alibaba = AlibabaCrawler()
    crawl_alibaba.crawl_all(1, 3) 
    
    end_time = datetime.now()
    print("Kết thúc:", end_time)
    print("Tổng thời gian:", end_time - start_time)