import requests
import pandas as pd
import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth
import sys
from urllib.parse import urlparse, parse_qs, quote
from datetime import datetime
import re
import unicodedata



class LazadaCaptchaError(Exception):
    pass

class LazadaCrawler:
    def __init__(self):
        self.all_results = []
        self.api_url = 'https://www.lazada.vn/catalog/'
        self.session = requests.Session()

        self.categories_list = [
            "Laptops", "Desktops Computers"
        ]

        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6',
            'priority': 'u=1, i',
            'referer': 'https://www.lazada.vn/',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'x-csrf-token': '',
            # 'cookie': '__wpkreporterwid_=797c7679-1840-4a06-39de-2b36eb5190b0; __itrace_wid=6edc91a8-a9c0-4e40-0a2d-a57c7632fd1e; t_fv=1766196841959; t_uid=240JDHVeXHQfo9mqVwkyEoVYP7Xj4NPe; lzd_cid=1bfc5350-29ea-4fee-b490-854eddde7098; cna=avTMIe0zTzcCAXRgLESTi6lq; hng=VN|en|VND|704; userLanguageML=en; lwrid=AgGbOYkNZVfFJfSIkNMGX39uI13Q; xlly_s=1; _lang=vi_VN; lzd_sid=1b0013067c19acd34549aa18b5fd9c35; _tb_token_=eb7110038617e; _m_h5_tk=d893b42cf43a6c6484d9681c9f6cd99e_1773320374663; _m_h5_tk_enc=00bae1caa16f3cd2100b174115a021ae; lwrtk=AAIEabMI3RsZFLCoZBdmXmWeQDe6ibYn32w/RfOznPmN88waxgAY9Hk=; LZD_WEB_TRACER_ROOT_SPAN_ID=46271c41b2857fa4; LZD_WEB_TRACER_TRACE_ID=506b59ea0f764977aa675ceb92319f30; t_sid=DbTyRMxiwSWqk4IFdGkWt1uO9fOS1n4Q; utm_channel=NA; x5sectag=52445; bx-cookie-test=1; x5sec=7b22617365727665722d6c617a6164613b33223a22617c434e667779733047454b54696a5a734249676c795a574e686348526a61474577397337642b762f2f2f2f2f2f415570714d44597759575a6d4d4441774d4441774d4441774d4441774d4441774d4441774d4441774d4441774d4441774d4441774d4441774e44426c5a6a67324d57497a4d5759774e6a51354d44646a5a6a677a4d4467774e5441774d4441774d4441774d44466959546c694d7a5a6b5a6a6c684f44426c4e4463344e5745314f474e6d5a546b785a44686b5954646a4f513d3d222c22733b32223a2265393536666433323362363235653132227d; isg=BE1NiJeiGJ7DjrxG-emYAwJrXGnHKoH8FFis14_SWORThm04V3sgzsBd8ALgRpm0; tfstk=fzfH8Ag8g9JQ0viHlRAQC0Ekx2eOODOWBghJ2QKzQh-svDhdzzAl-gf8Ra8REGjPqbUC2BnljB1OpbKLAQbPDQqYDSFARNABaoEv1LGiPQ8zw3uX8zsXNQrYXNCAFfA5xEo4wUbaSULSaYSyLF7wfUcEUg-eQc8DlQ-yPUgnqCiPayvDmmls4cTzlxKA8hccc1YETnVXjb5d_evhaw-MrUfM-exDEMGYb6SOz6CBCWlHNNBcqTS4XvKFnEjMH9qmtijBzaYPxSgDb6blsp6tYv8DtHvVTKP-ZwvPI1AdTuMfWNxenCBTCkpJtMXXcpy_fgbMvg5HQDjPjAkqb9GW7zCZFY9e5FxY2orKYM0liW4gSxzWLFTBDP4iFY9e5FxYSPD4Np86RnC..; epssw=11*mmLt2mhVHXS9dcvgEN0kjMt_dr91UKD7pIHJ659o9WQcil1FhrNTnvh1CFeTz6XHap426ihvez9dKqAZ3tv09tvOEOyvQKeiTNIZa7N2L3f8YY6teOAkP60x_mNpDmL9JAVT3TeZmmm-5p1neye01KUmBqgqOodUtbWslz5cceDScztoPzBmnoHu0_FoxoEyRTBi1K1uwoasRBHuuRmgBmHnkSq50IHcF_7t1lImmHGuu-7zIhfmBuuFf7uyFcuuuzTLlcuummmemvgaBja0lc3-c_jemvLaBjImAO3DWK9issgLDgeamB..',
        })

        initial_cookies = {}

        requests.utils.add_dict_to_cookiejar(self.session.cookies, initial_cookies)
    

    def refresh_session_manual(self, category="Mobiles"):
        encoded_q = quote(category)
        target_url = f"https://www.lazada.vn/catalog/?q={encoded_q}&service=all_channel"

        print("\n" + "!"*50)
        print(" [!] PHÁT HIỆN RECAPTCHA (I'M NOT A ROBOT)")
        print(" [!] VUI LÒNG TÍCH VÀO Ô TRONG CỬA SỔ TRÌNH DUYỆT")
        print("!"*50 + "\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            stealth = Stealth()
            stealth.apply_stealth_sync(page)

            try:
                page.goto(target_url, timeout=90000, wait_until="commit")
                print(">>> Đang trinh sát trang web (đợi 10 giây)...")
                page.wait_for_timeout(10000)
                
                captcha_container = ".baxia-dialog-content"
                captcha_iframe = "#baxia-dialog-content"
                is_resolved = False
                print(">>> Đang kiểm tra Captcha...")
                for _ in range(10):
                    if page.is_visible(captcha_container) or page.is_visible(captcha_iframe):
                        print("!!! ĐÃ THẤY BẢNG ROBOT")
                        print(">>> Đang đợi bạn thao tác tích vào ô 'I'm not a robot'...")
                        
                        page.wait_for_selector(captcha_container, state="hidden", timeout=120000)
                        input(">>> Nếu đã xác minh xong thì nhấn phím [ENTER] ở đây")
                        print("[+] Xác minh THÀNH CÔNG! Trang web đã trở lại bình thường.")
                        
                    if page.is_visible("[data-qa-locator='product-item']"):
                        print("[+] Đã thấy danh sách sản phẩm thực tế")
                        is_resolved = True
                        break
                    print("... Vẫn đang đợi trang web load sản phẩm ...")
                    page.wait_for_timeout(3000)

                if not is_resolved:
                    print(">>> CẢNH BÁO: Trang web vẫn chưa hiện sản phẩm.")
                    input(">>> HÃY NHẤN F5 TRÊN TRÌNH DUYỆT ĐẾN KHI HIỆN SẢN PHẨM RỒI NHẤN [ENTER] TẠI ĐÂY...")
                
                time.sleep(3)

                current_url = page.url
                parsed_url = urlparse(current_url)
                params_in_url = parse_qs(parsed_url.query)
                
                # Ưu tiên lấy spm từ URL thực tế, nếu không có dùng mã searchlist "trung tính"
                if 'spm' in params_in_url:
                    self.current_spm = params_in_url['spm'][0]
                else:
                    self.current_spm = "a2o4n.searchlist.cate_1"
            
            except Exception as e:
                print("[-] Quá thời gian chờ hoặc có lỗi xảy ra.")
                # print("[-] Không thể lấy được Session mới. Script sẽ dừng để bảo vệ IP.")
                raise LazadaCaptchaError(f"Gạt Captcha thất bại sau 2 phút: {e}")

            playwright_cookies = context.cookies()
            new_cookies = {c['name']: c['value'] for c in playwright_cookies}
            new_ua = page.evaluate("navigator.userAgent")

            requests.utils.add_dict_to_cookiejar(self.session.cookies, new_cookies)
            self.session.headers.update({
                'user-agent': new_ua,
                'x-csrf-token': new_cookies.get('_tb_token_', '')
            })
            browser.close() # Tự động đóng trình duyệt khi bạn đã gạt xong
            print("[+] Session đã được làm mới. Quay lại chế độ cào tự động...\n")

    def crawl_page(self, category, page):
        # ĐỒNG BỘ CSRF TOKEN (Mẹo để tránh bị chặn sau 50-100 trang)
        current_cookies = self.session.cookies.get_dict()
        if '_tb_token_' in current_cookies:
            self.session.headers['x-csrf-token'] = current_cookies['_tb_token_']
        
        params = {
            'ajax': 'true',
            'from': 'hp_categories',
            'page': str(page),
            'q': category,
            'service': 'all_channel',
            'spm': getattr(self, 'current_spm', 'a2o4n.searchlist.cate_1'),
            'src': 'all_channel',
        }

        if str(page) == '1':
            params['isFirstRequest'] = 'true'

        try:
            response = self.session.get(
                self.api_url, 
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                # SAU KHI REQUEST THÀNH CÔNG: 
                # Session sẽ tự động cập nhật các Cookie mới (Set-Cookie) nếu Lazada trả về.
                # Bạn có thể kiểm tra cookie hiện tại bằng cách:
                # print(self.session.cookies.get_dict()) 
                data = response.json()
                
                if ('action' in data and data['action'] == 'captcha') or 'RGV587_ERROR' in str(data):
                    # NẾU BỊ CHẶN -> GỌI HÀM GẠT TAY
                    self.refresh_session_manual(category)
                    # Sau khi gạt xong, thử cào lại chính trang này
                    return self.crawl_page(category, page)
                
                if 'ret' in data and any('FAIL' in r for r in data['ret']):
                    print(f"Lỗi hệ thống Lazada: {data['ret']}")
                    return None
                
                items = data.get('mods', {}).get('listItems', [])
                
                if not items:
                    total_results = data.get('mainInfo', {}).get('totalResults', '0')
                    print(f"Cảnh báo: Không có sản phẩm ở trang {page}. (Tổng kết quả: {total_results})")
                    return []
                print(f"Thành công: Trang {page} lấy được {len(items)} sản phẩm.")
                return items
            
            elif response.status_code == 403:
                print(f"Lỗi 403: IP của bạn đã bị Lazada đưa vào danh sách đen.")
                return None
            else:
                print(f"Loi {response.status_code} o trang {page}")
                return None
        except requests.exceptions.Timeout:
            print(f"Lỗi: Timeout ở trang {page}. Mạng yếu hoặc server Lazada quá tải.")
            return None
        except Exception as e:
            print(f"Có lỗi lạ xảy ra: {str(e)}")
            return None
        
    def crawl_category(self, category, page_start, page_end):
        results_category = []
        print(f"--- Bắt đầu cào dữ liệu ngành hàng {category} ---")

        for page in range(page_start, page_end + 1):
            if page % 10 == 0:
                print("Thời gian hiện tại:", datetime.now())
                time.sleep(random.uniform(80, 120))
            data = self.crawl_page(category=category, page=page)
            if data:
                for item in data:
                    product = {
                        'ID': item.get('itemId'),
                        'name': item.get('name'),
                        'brand_name': item.get('brandName'),
                        'price': item.get('price'),
                    }
                    results_category.append(product)
                print(f"Đã xong trang {page}. Các trang đã cào có tổng cộng: {len(results_category)} sản phẩm.")
                time.sleep(random.uniform(7, 12)) 
            else:
                print("Không lấy được dữ liệu nữa, dừng lại")
                break
        return results_category
    
    def crawl_all(self, page_start, page_end, path_csv):
        try:
            self.refresh_session_manual()

            for category in self.categories_list:
                res_category = self.crawl_category(category, page_start, page_end)
                self.all_results.extend(res_category)
            print("\n--- Hoàn thành ---")
        except LazadaCaptchaError as e:
            print(f"\n[!] DỪNG CÀO: {e}")
        except Exception as e:
            print(f"\n[!] Lỗi không xác định: {e}")
        finally:
            # Dù lỗi hay không cũng sẽ lưu dữ liệu đã cào được
            self.save_data_to_csv(path_csv)
            print("Thời gian kết thúc:", datetime.now())
        
    
    def save_data_to_csv(self, path_csv):
        df = pd.DataFrame(self.all_results)
        df.to_csv(path_csv, index=False, encoding="utf-8-sig")
        print(f"Đã lưu dữ liệu vào file {path_csv}")

    
if __name__ == "__main__":
    start_time = datetime.now()
    print("Thời gian bắt đầu:", start_time)
    crawl_lazada = LazadaCrawler()
    path_csv = r"F:\dai_hoc\2526_Ki_2\CDCNNB\ProductHunter\services\lazada_crawler\lazada_product.csv"
    crawl_lazada.crawl_all(1, 1, path_csv)
    end_time = datetime.now()
    print("Kết thúc:", end_time)
    print("Tổng thời gian:", end_time - start_time)