from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys
import time
import unicodedata
import urllib.parse
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth

from services.crawler.core.crawler import Crawler
from services.crawler.core.define.platform_type import PlatformType
from services.crawler.utils.text_parser import ProductNormalizer


class FptTrojanPro(Crawler):
    PLATFORM_ID = PlatformType.FPTSHOP
    PLATFORM_NAME = "FPT Shop"
    PLATFORM_BASE_URL = "https://fptshop.com.vn"
    BATCH_SIZE = 200

    def __init__(self, output_dir: Optional[str] = None):
        base_url = self.PLATFORM_BASE_URL
        output_dir = output_dir or str(Path(__file__).resolve().parent)
        super().__init__(name="fptshop", output_dir=output_dir, base_url=base_url)
        self.products: List[Dict[str, object]] = []
        self.platform_products: List[Dict[str, object]] = []
        self.normalizer = ProductNormalizer()
        
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

    def extract_brand(self, name: str) -> str:
        """Đoán hãng sản xuất từ tên sản phẩm để chia cột cho đẹp"""
        if not name:
            return "FPT Shop"
        words = name.split()
        brand = words[0].capitalize()
        
        # Lọc bỏ các danh từ chung chung đứng ở đầu tên
        if brand.lower() in ["điện", "máy", "laptop", "pc", "màn", "tủ", "lò", "nồi", "bếp", "quạt", "robot", "loa"]:
            if len(words) >= 3:
                brand = words[2].capitalize() if brand.lower() in ["điện", "máy"] else words[1].capitalize()
        return brand

    def _slugify(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = text.lower()
        text = "".join(ch if ch.isalnum() else "-" for ch in text)
        text = "-".join(part for part in text.split("-") if part)
        return text

    def _normalize_name(self, name: str) -> str:
        raw = self.normalizer.normalize(name)
        text = unicodedata.normalize("NFKD", raw)
        text = text.encode("ascii", "ignore").decode("ascii")
        return " ".join(text.split())

    def _parse_price(self, price: str) -> Optional[Decimal]:
        if not price:
            return None
        cleaned = "".join(ch for ch in price if ch.isdigit())
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def _extract_original_item_id(self, url: str, fallback: str) -> str:
        if not url:
            return fallback
        parsed = urllib.parse.urlparse(url)
        slug = parsed.path.rstrip("/").split("/")[-1]
        return slug or fallback

    def _platform_id(self) -> int:
        value = self.PLATFORM_ID
        if isinstance(value, tuple):
            value = value[0] if value else 0
        return int(value)

    def parse_product_block(self, block, category: str) -> Optional[Tuple[Dict[str, object], Dict[str, object]]]:
        """Bóc tách thông tin chuẩn từ khối HTML"""
        # Lấy Tên & Link
        name_tag = block.find('h3', class_=lambda c: isinstance(c, str) and 'cardTitle' in c)
        if not name_tag or not name_tag.find('a'): return None
        
        name = name_tag.find('a').get('title', '').strip() or name_tag.text.strip()
        if len(name) < 5: return None
        
        link_tag = name_tag.find('a', href=True)
        base_url = self.base_url or ""
        url = urllib.parse.urljoin(base_url, link_tag['href']) if link_tag else ""

        # Lấy Giá
        price_container = block.find('div', class_=lambda c: isinstance(c, str) and 'cardInfo' in c)
        price = ''
        if price_container:
            price_tag = price_container.find('p', class_=lambda c: isinstance(c, str) and 'b1-semibold' in c)
            if price_tag:
                 price = price_tag.text.strip()
            else:
                 price_tags = price_container.find_all(string=lambda text: text and ('₫' in text or 'đ' in text.lower()))
                 if price_tags: price = price_tags[0].strip()

        # Lấy Ảnh
        img_container = block.find('div', class_=lambda c: isinstance(c, str) and 'relative' in c)
        img_url = None
        if img_container:
            img_tag = img_container.find('img')
            if img_tag:
                srcset = img_tag.get('srcset')
                img_url = srcset.split(',')[0].split(' ')[0].strip() if srcset else img_tag.get('src')

        brand = self.extract_brand(name)

        normalized_name = self._normalize_name(name)
        product_slug = self._slugify(name) or self._slugify(normalized_name)
        original_item_id = self._extract_original_item_id(url, product_slug or normalized_name)
        current_price = self._parse_price(price)

        product = {
            "normalized_name": normalized_name,
            "slug": product_slug,
            "brand": brand,
            "category": category,
            "main_image_url": img_url,
        }

        platform_product = {
            "product_id": None,
            "platform_id": self._platform_id(),
            "raw_name": name,
            "original_item_id": original_item_id,
            "url": url,
            "affiliate_url": None,
            "current_price": current_price,
            "original_price": None,
            "in_stock": True,
            "last_crawled_at": datetime.now(timezone.utc).isoformat(),
        }

        return product, platform_product

    def _chunk(self, items: List[Dict[str, object]]) -> Iterable[List[Dict[str, object]]]:
        for i in range(0, len(items), self.BATCH_SIZE):
            yield items[i:i + self.BATCH_SIZE]

    def _dedupe_products(self, products: List[Dict[str, object]]) -> List[Dict[str, object]]:
        by_slug: Dict[str, Dict[str, object]] = {}
        for product in products:
            slug = str(product.get("slug") or "")
            if not slug:
                continue
            by_slug[slug] = product
        return list(by_slug.values())

    def _dedupe_platform_products(self, platform_products: List[Dict[str, object]]) -> List[Dict[str, object]]:
        by_key: Dict[Tuple[object, object], Dict[str, object]] = {}
        for record in platform_products:
            key = (record.get("platform_id"), record.get("original_item_id"))
            if key[0] is None or key[1] in (None, ""):
                continue
            by_key[key] = record
        return list(by_key.values())

    def _db_is_sqlite(self) -> bool:
        db_url = getattr(self.storage.get_db_handler(), "db_url", "")
        scheme = urlparse(str(db_url)).scheme.lower()
        return scheme in {"", "sqlite"}

    def _upsert_products(self, products: List[Dict[str, object]]) -> None:
        if not products:
            return
        db = self.storage.get_db_handler()
        placeholder = "?" if self._db_is_sqlite() else "%s"
        values = []
        for product in products:
            values.append(
                (
                    product.get("normalized_name"),
                    product.get("slug"),
                    product.get("brand"),
                    product.get("category"),
                    product.get("main_image_url"),
                )
            )
        sql = (
            "INSERT INTO products (normalized_name, slug, brand, category, main_image_url) "
            f"VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder}) "
            "ON CONFLICT (slug) DO UPDATE SET "
            "normalized_name=EXCLUDED.normalized_name, "
            "brand=EXCLUDED.brand, "
            "category=EXCLUDED.category, "
            "main_image_url=EXCLUDED.main_image_url"
        )
        db.executemany(sql, values)

    def _ensure_platform(self) -> None:
        db = self.storage.get_db_handler()
        platform_id = self._platform_id()
        placeholder = "?" if self._db_is_sqlite() else "%s"
        sql = (
            "INSERT INTO platforms (id, name, base_url, affiliate_config) "
            f"VALUES ({placeholder},{placeholder},{placeholder},{placeholder}) "
            "ON CONFLICT (id) DO UPDATE SET "
            "name=EXCLUDED.name, "
            "base_url=EXCLUDED.base_url, "
            "affiliate_config=EXCLUDED.affiliate_config"
        )
        db.query(sql, [platform_id, self.PLATFORM_NAME, self.PLATFORM_BASE_URL, None])

    def _fetch_product_ids(self, slugs: List[str]) -> Dict[str, str]:
        if not slugs:
            return {}
        db = self.storage.get_db_handler()
        placeholder = "?" if self._db_is_sqlite() else "%s"
        markers = ", ".join([placeholder] * len(slugs))
        sql = f"SELECT id, slug, normalized_name FROM products WHERE slug IN ({markers})"
        rows = db.query(sql, slugs)
        id_by_slug: Dict[str, str] = {}
        for row in rows:
            slug = str(row.get("slug") or "")
            if not slug:
                continue
            id_by_slug[slug] = str(row.get("id"))
        return id_by_slug

    def _upsert_platform_products(self, platform_products: List[Dict[str, object]]) -> None:
        if not platform_products:
            return
        db = self.storage.get_db_handler()
        placeholder = "?" if self._db_is_sqlite() else "%s"
        values = []
        for record in platform_products:
            values.append(
                (
                    record.get("product_id"),
                    record.get("platform_id"),
                    record.get("raw_name"),
                    record.get("original_item_id"),
                    record.get("url"),
                    record.get("affiliate_url"),
                    record.get("current_price"),
                    record.get("original_price"),
                    record.get("in_stock"),
                    record.get("last_crawled_at"),
                )
            )
        sql = (
            "INSERT INTO platform_products (product_id, platform_id, raw_name, original_item_id, url, "
            "affiliate_url, current_price, original_price, in_stock, last_crawled_at) "
            f"VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder}) "
            "ON CONFLICT (platform_id, original_item_id) DO UPDATE SET "
            "product_id=EXCLUDED.product_id, "
            "raw_name=EXCLUDED.raw_name, "
            "url=EXCLUDED.url, "
            "affiliate_url=EXCLUDED.affiliate_url, "
            "current_price=EXCLUDED.current_price, "
            "original_price=EXCLUDED.original_price, "
            "in_stock=EXCLUDED.in_stock, "
            "last_crawled_at=EXCLUDED.last_crawled_at"
        )
        db.executemany(sql, values)

    def _resolve_product_id(
        self,
        product: Dict[str, object],
        cache: Dict[str, str],
        typesense,
        typesense_state: Dict[str, bool],
    ) -> Optional[str]:
        slug = str(product.get("slug") or "")
        normalized = str(product.get("normalized_name") or "")
        cache_key = slug or normalized
        if cache_key and cache_key in cache:
            return cache[cache_key]

        if typesense_state.get("enabled") and (normalized or slug):
            query = normalized or slug
            try:
                result = typesense.search("products", query=query)
                hits = result.get("hits") or []
                if hits:
                    doc = hits[0].get("document") or {}
                    doc_id = doc.get("id")
                    if doc_id:
                        resolved = str(doc_id)
                        if slug:
                            cache[slug] = resolved
                        if normalized:
                            cache[normalized] = resolved
                        return resolved
            except Exception as exc:
                typesense_state["enabled"] = False
                print(f"[!] Typesense search failed: {exc}")

        if not slug:
            return None

        self._upsert_products([product])
        product_ids = self._fetch_product_ids([slug])
        resolved = product_ids.get(slug)
        if not resolved:
            return None

        if slug:
            cache[slug] = resolved
        if normalized:
            cache[normalized] = resolved

        if typesense_state.get("enabled"):
            try:
                typesense.upsert_document(
                    "products",
                    {
                        "id": str(resolved),
                        "normalized_name": normalized or "",
                        "slug": slug,
                    },
                )
            except Exception as exc:
                typesense_state["enabled"] = False
                print(f"[!] Typesense update failed: {exc}")

        return resolved

    def persist_batch(self, parsed_items: List[Tuple[Dict[str, object], Dict[str, object]]]) -> None:
        if not parsed_items:
            return

        self._ensure_platform()

        typesense = self.storage.get_typesense_handler()
        typesense_state = {"enabled": True}
        try:
            typesense.ensure_collection()
        except Exception as exc:
            typesense_state["enabled"] = False
            print(f"[!] Typesense unavailable: {exc}")

        cache: Dict[str, str] = {}
        platform_products: List[Dict[str, object]] = []

        for product, platform_product in parsed_items:
            product_id = self._resolve_product_id(product, cache, typesense, typesense_state)
            if not product_id:
                continue
            platform_product["product_id"] = product_id
            platform_products.append(platform_product)

        platform_products = self._dedupe_platform_products(platform_products)
        for chunk in self._chunk(platform_products):
            self._upsert_platform_products(chunk)

    def crawl(self) -> None:
        start_time = datetime.now()
        print(f"\n[+] KHỞI ĐỘNG CHIẾN DỊCH CÀO TOÀN BỘ FPT SHOP - {start_time}")
        
        with sync_playwright() as p:
            # Mở trình duyệt có giao diện để dễ theo dõi
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]) 
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            for category in self.categories:
                # KỸ THUẬT TIẾT KIỆM RAM: Mở Tab mới cho mỗi danh mục, xài xong đóng lại
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                
                base_url = self.base_url or ""
                url = f"{base_url}/{category}"
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
                    product_blocks = soup.find_all('div', class_=lambda c: isinstance(c, str) and 'cardDefault' in c)
                    
                    parsed_items = []
                    for block in product_blocks:
                        result = self.parse_product_block(block, category)
                        if result:
                            parsed_items.append(result)
                         
                    print(f"[+] Bóc tách thành công {len(parsed_items)} sản phẩm ngành {category}.")
                     
                    self.persist_batch(parsed_items)

                    # Cộng dồn dữ liệu và LƯU FILE NGAY LẬP TỨC để phòng ngừa sự cố
                    for product, platform_product in parsed_items:
                        self.products.append(product)
                        self.platform_products.append(platform_product)
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
        if not self.products and not self.platform_products:
            return

        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if self.products:
            products_df = pd.DataFrame(self.products)
            products_df = products_df.drop_duplicates(subset=["slug"], keep="first")
            products_df = products_df.dropna(subset=["slug", "normalized_name"])
            products_file = output_path / "fpt_products.csv"
            products_df.to_csv(products_file, index=False, encoding="utf-8-sig")
            print(f" [LƯU TRỮ AN TOÀN] Đã cập nhật file {products_file} | Tổng: {len(products_df)} sản phẩm.")

        if self.platform_products:
            platform_df = pd.DataFrame(self.platform_products)
            platform_df = platform_df.drop_duplicates(subset=["platform_id", "original_item_id"], keep="first")
            platform_df = platform_df.dropna(subset=["platform_id", "original_item_id", "url"])
            platform_file = output_path / "fpt_platform_products.csv"
            platform_df.to_csv(platform_file, index=False, encoding="utf-8-sig")
            print(f" [LƯU TRỮ AN TOÀN] Đã cập nhật file {platform_file} | Tổng: {len(platform_df)} listing.")

if __name__ == "__main__":
    try:
        crawler = FptTrojanPro()
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n[!] Bạn đã nhấn Ctrl+C. Hệ thống dừng khẩn cấp!")
        sys.exit(0)
