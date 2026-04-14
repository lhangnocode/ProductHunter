from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys
import time
import unicodedata
import urllib.parse
from typing import Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth

from services.crawler.core.crawler import Crawler
from services.crawler.core.define.platform_type import PlatformType
from services.crawler.utils.text_parser import ProductNormalizer


class PhongVuCrawler(Crawler):
    PLATFORM_ID = PlatformType.PHONGVU
    PLATFORM_NAME = "Phong Vũ"
    PLATFORM_BASE_URL = "https://phongvu.vn"
    BATCH_SIZE = 200

    def __init__(self, output_dir: Optional[str] = None):
        base_url = self.PLATFORM_BASE_URL
        output_dir = output_dir or str(Path(__file__).resolve().parent)
        super().__init__(name="phongvu", output_dir=output_dir, base_url=base_url)
        self.products: List[Dict[str, object]] = []
        self.platform_products: List[Dict[str, object]] = []
        self.normalizer = ProductNormalizer()

        # Danh mục chuẩn của Phong Vũ (Slug)
        self.categories = [
            "c/laptop", "c/apple", "c/dien-may", "c/dien-gia-dung",
            "c/pc", "c/man-hinh-may-tinh", "c/linh-kien-may-tinh",
            "c/phu-kien", "c/gaming-gear", "c/dien-thoai-tablet",
            "c/thiet-bi-am-thanh", "c/thiet-bi-van-phong",
        ]

    def extract_brand(self, name: str) -> str:
        """Đoán hãng sản xuất từ tên sản phẩm"""
        if not name:
            return "Phong Vũ"
        words = name.split()
        brand = words[0].capitalize()

        if brand.lower() in [
            "laptop", "pc", "màn", "chuột", "bàn", "tai", "loa", "tivi",
            "máy", "điện", "apple", "vỏ", "nguồn", "ổ", "ram", "card",
            "cpu", "mainboard",
        ]:
            if len(words) >= 3:
                if brand.lower() in ["máy", "điện", "ổ", "card", "màn", "tai"]:
                    brand = words[2].capitalize()
                else:
                    brand = words[1].capitalize()
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

    def scroll_and_load_all(self, page):
        """Hàm tự động cuộn và đấm nút 'Xem thêm sản phẩm' liên tục"""
        try:
            print("[*] Đang rà soát và tắt Popup...")
            page.mouse.click(10, 10)
            page.wait_for_timeout(1000)
        except Exception:
            pass

        click_count = 0
        stuck_counter = 0

        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight - 800);")
            page.wait_for_timeout(1500)

            count_before = page.locator("text='₫'").count()

            try:
                clicked = page.evaluate(
                    """
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
                    """
                )

                if not clicked:
                    print("[*] Không tìm thấy nút 'Xem thêm sản phẩm'. Đã cào đến đáy danh mục!")
                    break

                print(f"[*] Đã bấm 'Xem thêm sản phẩm' lần {click_count + 1} (Đang có {count_before} SP). Chờ tải...")

                is_loaded = False
                for _ in range(15):
                    page.wait_for_timeout(1000)
                    if page.locator("text='₫'").count() > count_before:
                        is_loaded = True
                        break

                if is_loaded:
                    click_count += 1
                    stuck_counter = 0
                else:
                    stuck_counter += 1
                    if stuck_counter >= 5:
                        print(f"\n[!] PHÁT HIỆN NÚT ZOMBIE: Thử 5 lần nhưng web ngừng nhả dữ liệu. Rút lui với {count_before} SP!")
                        break
                    print(f"[*] Cảnh báo kẹt ({stuck_counter}/5): Mạng chậm, sẽ cuộn và thử click lại...")

            except Exception as e:
                print(f"[*] Lỗi tương tác nút: {e}. Dừng tải.")
                break

        print("[*] Hoàn tất bung HTML. Đang cuộn rà soát để tải ảnh sắc nét...")
        page.evaluate("window.scrollTo(0, 0);")
        total_items = page.locator("text='₫'").count()
        scroll_steps = int(total_items / 10) + 3
        for _ in range(scroll_steps):
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(300)
        page.wait_for_timeout(2000)

    def parse_product_block(
        self,
        p_tag,
        category: str,
        seen_links: Set[str],
    ) -> Optional[Tuple[Dict[str, object], Dict[str, object]]]:
        """Thuật toán mỏ neo: leo từ chữ '₫' lên thẻ bọc ngoài để lấy thông tin"""
        parent = p_tag.parent
        for _ in range(6):
            if not parent:
                break

            link_tag = parent.find("a", href=True)
            img_tag = parent.find("img")

            if link_tag and img_tag:
                href = link_tag["href"]
                base_url = self.base_url or ""
                url = urllib.parse.urljoin(base_url, href)

                if any(bad in url for bad in ["help.", "/p/he-thong"]):
                    return None

                if url in seen_links:
                    return None

                seen_links.add(url)

                name_tag = parent.find(
                    ["h3", "div"],
                    class_=lambda c: isinstance(c, str) and ("product-name" in c.lower() or "title" in c.lower()),
                )
                name = name_tag.text.strip() if name_tag else link_tag.text.strip()
                if len(name) < 5:
                    return None

                price = p_tag.parent.text.strip()
                img_url = img_tag.get("src") or img_tag.get("data-src")
                brand = self.extract_brand(name)

                normalized_name = self._normalize_name(name)
                product_slug = self._slugify(name) or self._slugify(normalized_name)
                original_item_id = self._extract_original_item_id(url, product_slug or normalized_name)
                current_price = self._parse_price(price)
                category_name = category.replace("c/", "", 1)

                product = {
                    "normalized_name": normalized_name,
                    "slug": product_slug,
                    "brand": brand,
                    "category": category_name,
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
            parent = parent.parent
        return None

    def _platform_id(self) -> int:
        value = self.PLATFORM_ID
        if isinstance(value, tuple):
            value = value[0] if value else 0
        return int(value)

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

    def crawl(self) -> None:
        start_time = datetime.now()
        print(f"\n[+] KHỞI ĐỘNG CỖ MÁY CÀO PHONG VŨ - {start_time}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

            for category in self.categories:
                page = context.new_page()
                Stealth().apply_stealth_sync(page)

                base_url = self.base_url or ""
                url = f"{base_url}/{category}"
                print(f"\n{'='*60}\n>>> MỤC TIÊU MỚI: {url}\n{'='*60}")

                try:
                    page.goto(url, timeout=90000, wait_until="domcontentloaded")
                    self.scroll_and_load_all(page)

                    soup = BeautifulSoup(page.content(), "html.parser")
                    price_tags = soup.find_all(string=lambda text: bool(text) and "₫" in text)

                    parsed_items: List[Tuple[Dict[str, object], Dict[str, object]]] = []
                    seen_links: Set[str] = set()

                    for p_tag in price_tags:
                        result = self.parse_product_block(p_tag, category, seen_links)
                        if result:
                            parsed_items.append(result)

                    print(f"[+] Bóc tách thành công {len(parsed_items)} sản phẩm ngành {category}.")

                    for product, platform_product in parsed_items:
                        self.products.append(product)
                        self.platform_products.append(platform_product)
                    self.clean_and_save()

                except Exception as e:
                    print(f"[-] Bỏ qua danh mục {category} do gặp lỗi: {e}")

                finally:
                    page.close()
                    time.sleep(2)

            browser.close()

            end_time = datetime.now()
            print("\n" + "#" * 60)
            print(f"[+] CHIẾN DỊCH HOÀN TẤT! TỔNG THỜI GIAN: {end_time - start_time}")
            print("#" * 60 + "\n")

    def clean_and_save(self) -> None:
        if not self.products and not self.platform_products:
            return

        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if self.products:
            products_df = pd.DataFrame(self.products)
            products_df = products_df.drop_duplicates(subset=["slug"], keep="first")
            products_df = products_df.dropna(subset=["slug", "normalized_name"])
            products_file = output_path / "phongvu_products.csv"
            products_df.to_csv(products_file, index=False, encoding="utf-8-sig")
            print(f"   ↳ [ĐÃ LƯU] File {products_file} | Tổng: {len(products_df)} sản phẩm.")

        if self.platform_products:
            platform_df = pd.DataFrame(self.platform_products)
            platform_df = platform_df.drop_duplicates(subset=["platform_id", "original_item_id"], keep="first")
            platform_df = platform_df.dropna(subset=["platform_id", "original_item_id", "url"])
            platform_file = output_path / "phongvu_platform_products.csv"
            platform_df.to_csv(platform_file, index=False, encoding="utf-8-sig")
            print(f"   ↳ [ĐÃ LƯU] File {platform_file} | Tổng: {len(platform_df)} listing.")


if __name__ == "__main__":
    try:
        crawler = PhongVuCrawler()
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n[!] Nhận lệnh ngắt Ctrl+C. Hệ thống dừng an toàn!")
        sys.exit(0)
