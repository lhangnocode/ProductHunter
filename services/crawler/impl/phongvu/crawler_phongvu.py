from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys
import re
import time
from typing import List, Optional

from playwright.sync_api import ElementHandle, sync_playwright
from playwright_stealth.stealth import Stealth

from services.crawler.models.raw_product import RawProduct

PLATFORM_ID = 8
PLATFORM_BASE_URL = "https://phongvu.vn"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "output"

CATEGORY_MAP: dict[str, str] = {
    "c/laptop":                 "laptop",
    "c/apple":                  "smartphone",
    "c/dien-thoai-tablet":      "smartphone",
    "c/man-hinh-may-tinh":      "monitor",
    "c/pc":                     "desktop",
    "c/linh-kien-may-tinh":     "pc_component",
    "c/thiet-bi-am-thanh":      "speaker",
    "c/gaming-gear":            "peripheral",
    "c/phu-kien":               "peripheral",
    "c/thiet-bi-van-phong":     "peripheral",
    "c/dien-may":               "appliance",
    "c/dien-gia-dung":          "houseware",
}


class PhongVuCrawler:
    parent_selector = "div.grow"
    product_card = "div[class*='product'], div.relative"

    def __init__(self, output_dir: Optional[str] = None):
        self.platform_id = PLATFORM_ID
        self.base_url = PLATFORM_BASE_URL
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def crawl(self) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--no-sandbox", "--disable-setuid-sandbox"])
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

            for category_slug, category_name in CATEGORY_MAP.items():
                page = context.new_page()
                Stealth().apply_stealth_sync(page)

                category_url = f"{self.base_url}/{category_slug}"
                print(f"Crawling category: {category_name} ({category_slug})")
                page.goto(category_url, timeout=90000, wait_until="domcontentloaded")
                time.sleep(3)

                # Click "Xem thêm" until it disappears
                while True:
                    try:
                        xem_them_button = page.query_selector("a.css-b0m1yo")
                        if not xem_them_button:
                            break
                        xem_them_button.click()
                        time.sleep(2)  # Wait for new products to load
                    except Exception as e:
                        print(f"Error clicking 'Xem thêm': {e}")
                        break

                product_elements = page.query_selector_all(self.product_card)
                print(f"Found {len(product_elements)} products in category '{category_name}'")

                products: List[RawProduct] = []
                for elem in product_elements:
                    try:
                        product = self._extract_product_data(elem, category_name)
                        if product:
                            products.append(product)
                    except Exception as e:
                        print(f"Error extracting product data: {e}")

                self._save_to_csv(products)
                page.close()
                time.sleep(2)

            browser.close()

    def _extract_product_data(self, elem: ElementHandle, category_name: str) -> Optional[RawProduct]:
        try:
            name_elem = elem.query_selector("h3, [class*='product-name'], [class*='title']")
            name = name_elem.inner_text().strip() if name_elem else None
            if not name:
                return None

            url_elem = elem.query_selector("a")
            url = url_elem.get_attribute("href") if url_elem else None
            if not url:
                return None
            if url and not url.startswith("http"):
                url = self.base_url + url
            if any(bad in url for bad in ["help.", "/p/he-thong"]):
                return None

            price_text = self._extract_price_text(elem)
            current_price = self._parse_price(price_text)

            if current_price == 0 or current_price is None:
                return None

            original_price_elem = elem.query_selector("div.att-product-detail-retail-price.css-18z00w6]")
            original_price_text = original_price_elem.inner_text().strip() if original_price_elem else None
            original_price = self._parse_price(original_price_text) if original_price_text else None

            image_elem = elem.query_selector("img")
            image_url = None
            if image_elem:
                image_url = (
                    image_elem.get_attribute("src")
                    or image_elem.get_attribute("data-src")
                    or image_elem.get_attribute("data-srcset")
                )

            print(f"[phongvu] {name} - {price_text} - {url}")

            return RawProduct(
                platform_id=self.platform_id,
                raw_name=name,
                url=url,
                current_price=current_price,
                original_price=original_price,
                category=category_name,
                main_image_url=image_url,
                crawled_at=datetime.now(timezone.utc),
            )
        except Exception:
            return None

    def _extract_price_text(self, elem: ElementHandle) -> str:
        price_elem = elem.query_selector("[class*='price']")
        if price_elem:
            text = price_elem.inner_text().strip()
            if text:
                return text
        try:
            text = elem.inner_text()
        except Exception:
            return "0"
        matches = re.findall(r"\d[\d\.,]*\s*₫", text)
        if matches:
            return matches[-1]
        if "₫" in text:
            return "₫"
        return "0"

    def _parse_price(self, price_text: str) -> Decimal:
        try:
            cleaned = "".join(c for c in price_text if c.isdigit() or c in ",.").replace(",", "").replace(".", "")
            return Decimal(cleaned)
        except InvalidOperation:
            return Decimal(0)

    def _save_to_csv(self, products: List[RawProduct]) -> None:
        if not products:
            return
        output_file = self.output_dir / "phongvu_products.csv"
        with output_file.open("a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(RawProduct.csv_headers())
            for product in products:
                writer.writerow(product.to_csv_row())
        print(f"Saved {len(products)} products to {output_file}")