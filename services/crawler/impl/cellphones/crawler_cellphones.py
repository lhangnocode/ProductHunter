from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import time
from typing import List, Optional

from playwright.sync_api import ElementHandle, sync_playwright
from playwright_stealth.stealth import Stealth

from services.crawler.models.raw_product import RawProduct

PLATFORM_ID = 9
PLATFORM_BASE_URL = "https://cellphones.com.vn"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "output"

CATEGORY_MAP: dict[str, str] = {
    "mobile.html":               "smartphone",
    "laptop.html":               "laptop",
    "tablet.html":        "tablet",
    "do-choi-cong-nghe.html":   "wearable",
    "thiet-bi-am-thanh.html":             "headphone",
    "man-hinh.html":    "monitor",
}


# Flow: Click "Xem thêm" -> Get device cards -> For each card, get element -> Extract data -> Save to CSV

class CellphonesCrawler:
    product_card = "div.product-info"

    def __init__(self, output_dir: Optional[str] = None):
        self.platform_id = PLATFORM_ID
        self.base_url = PLATFORM_BASE_URL
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def crawl(self) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            context = browser.new_context()
            page = context.new_page()
            Stealth().apply_stealth_sync(page)

            for category_slug, category_name in CATEGORY_MAP.items():
                print(f"Crawling category: {category_name} ({category_slug})")
                category_url = f"{self.base_url}/{category_slug}"
                page.goto(category_url, timeout=60000)
                time.sleep(2)  # Wait for initial load

                # Click "Xem thêm" until it disappears
                while True:
                    try:
                        xem_them_button = page.query_selector("a.button.btn-show-more.button__show-more-product")
                        if not xem_them_button:
                            break
                        xem_them_button.click()
                        time.sleep(2)  # Wait for new products to load
                    except Exception as e:
                        print(f"Error clicking 'Xem thêm': {e}")
                        break

                # Get product cards
                product_elements = page.query_selector_all(self.product_card)
                print(f"Found {len(product_elements)} products in category '{category_name}'")

                products = []
                for elem in product_elements:
                    try:
                        product = self._extract_product_data(elem, category_name)
                        if product:
                            products.append(product)
                    except Exception as e:
                        print(f"Error extracting product data: {e}")

                # Save to CSV
                self._save_to_csv(products)

            browser.close()

    def _extract_product_data(self, elem: ElementHandle, category_name: str) -> Optional[RawProduct]:
        try:
            name_elem = elem.query_selector("h3")
            name = name_elem.inner_text().strip() if name_elem else None
            if not name:
                return None

            url_elem = elem.query_selector("a")
            url = url_elem.get_attribute("href") if url_elem else None
            if not url:
                return None
            if not url.startswith("http"):
                url = self.base_url + url

            # TODO: add selector for current price
            current_price_elem = elem.query_selector("p.product__price--show")
            current_price_text = current_price_elem.inner_text().strip() if current_price_elem else None
            current_price = self._parse_price(current_price_text) if current_price_text else None

            if not current_price or current_price == 0:
                print(f"Skipping product with invalid price: {name}")
                return None

            # TODO: add selector for original / list price
            original_price_elem = elem.query_selector("p.product__price--through")
            original_price_text = original_price_elem.inner_text().strip() if original_price_elem else None
            original_price = self._parse_price(original_price_text) if original_price_text else None

            image_elem = elem.query_selector("img")
            image_url = image_elem.get_attribute("src") if image_elem else None

            print(f"[cellphones] {name} - {current_price_text} - {url}")

            return RawProduct(
                platform_id=self.platform_id,
                raw_name=name,
                url=url,
                current_price=current_price,
                original_price=original_price,
                category=category_name,
                main_image_url=image_url,
                crawled_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            print(f"Error in _extract_product_data: {e}")
            return None

    def _parse_price(self, price_text: str) -> Decimal:
        try:
            cleaned = ''.join(c for c in price_text if c.isdigit() or c in ',.').replace(',', '').replace('.', '')
            return Decimal(cleaned)
        except InvalidOperation:
            return Decimal(0)

    def _save_to_csv(self, products: List[RawProduct]) -> None:
        if not products:
            return
        output_file = self.output_dir / "cellphones_products.csv"
        write_header = not output_file.exists()
        with output_file.open('a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(RawProduct.csv_headers())
            for product in products:
                writer.writerow(product.to_csv_row())
        print(f"Saved {len(products)} products to {output_file}")


def crawl(output_dir: Path = OUTPUT_DIR) -> None:
    crawler = CellphonesCrawler(output_dir=str(output_dir))
    crawler.crawl()


if __name__ == "__main__":
    crawl()
