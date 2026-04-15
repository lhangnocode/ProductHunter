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

PLATFORM_ID = 7
PLATFORM_BASE_URL = "https://fptshop.com.vn"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "output"

CATEGORY_MAP: dict[str, str] = {
    "dien-thoai":           "smartphone",
    "may-tinh-xach-tay":    "laptop",
    "may-tinh-bang":        "tablet",
    "may-tinh-de-ban":      "desktop",
    "man-hinh":             "monitor",
    "dong-ho-thong-minh":   "wearable",
    "linh-kien-may-tinh":   "pc_component",
    "thiet-bi-mang":        "networking",
    "smart-home":           "smart_home",
    "may-in":               "peripheral",
    "tivi":                 "tv",
    "dieu-hoa":             "appliance",
    "tu-lanh":              "appliance",
    "tu-dong":              "appliance",
    "may-giat":             "appliance",
    "may-say-quan-ao":      "appliance",
    "robot-hut-bui":        "houseware",
    "may-hut-bui":          "houseware",
    "may-loc-khong-khi":    "houseware",
    "may-hut-am":           "houseware",
    "quat":                 "houseware",
    "may-loc-nuoc":         "houseware",
    "cay-nuoc-nong-lanh":   "houseware",
    "may-massage":          "houseware",
    "may-say-toc":          "houseware",
    "noi-chien-khong-dau":  "houseware",
    "lo-vi-song":           "houseware",
    "lo-nuong":             "houseware",
    "bep-nuong-dien":       "houseware",
    "may-rua-bat":          "houseware",
    "may-hut-mui":          "houseware",
    "noi-com-dien":         "houseware",
    "am-sieu-toc":          "houseware",
    "may-xay-sinh-to":      "houseware",
    "bep-dien-tu":          "houseware",
    "noi-ap-suat":          "houseware",
}


# Flow: Click "Xem thêm" -> Get device cards -> For each card, get element -> Extract data -> Save to CSV

class FPTShopCrawler:
    parent_selector = "div.grow"
    product_card = "div.group.relative.flex.h-full.flex-col.justify-between.relative"
    
    def __init__(self, output_dir: Optional[str] = None):
        self.platform_id = PLATFORM_ID
        self.base_url = PLATFORM_BASE_URL
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def crawl(self) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            
            # Loop over categories
            for category_slug, category_name in CATEGORY_MAP.items():
                print(f"Crawling category: {category_name} ({category_slug})")
                category_url = f"{self.base_url}/{category_slug}"
                page.goto(category_url, timeout=60000)
                time.sleep(3)  # Wait for initial load
                
                # Click "Xem thêm" until it disappears
                while True:
                    try:
                        xem_them_button = page.query_selector("button.flex.items-center.justify-center.transition-all.duration-300.ease-out.relative.rounded-3xl.text-sm.font-medium.leading-5.bg-bgWhiteDefault.text-textOnWhitePrimary.border.border-iconDividerOnWhite.px-4.py-2")
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
            name_elem = elem.query_selector("h3.mb-1")
            name = name_elem.inner_text().strip() if name_elem else "Unknown"
            
            url_elem = elem.query_selector("a")
            url = url_elem.get_attribute("href") if url_elem else None
            if url and not url.startswith("http"):
                url = self.base_url + url
            
            price_elem = elem.query_selector("p.text-textOnWhitePrimary.transition-all.duration-300.b1-semibold")
            price_text = price_elem.inner_text().strip() if price_elem else "0"
            price = self._parse_price(price_text)
            
            if price == 0 or price is None:
                print(f"Skipping product with invalid price: {name} - {price_text}")
                return None
            
            image_elem = elem.query_selector("img")
            image_url = image_elem.get_attribute("srcset") if image_elem else None
            
            print(f"[fpt] {name} - {price_text} - {url}")
            
            return RawProduct(
                platform_id=self.platform_id,
                raw_name=name,
                url=url,
                price=price,
                category=category_name,
                main_image_url=image_url,
                crawled_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            print(f"Error in _extract_product_data: {e}")
            return None
        
    def _parse_price(self, price_text: str) -> Decimal:
        try:
            # Remove non-digit characters (except for decimal separator)
            cleaned = ''.join(c for c in price_text if c.isdigit() or c in ',.').replace(',', '').replace('.', '')
            return Decimal(cleaned)
        except InvalidOperation:
            return Decimal(0)
    
    def _save_to_csv(self, products: List[RawProduct]) -> None:
        if not products:
            return
        output_file = self.output_dir / f"fptshop_products.csv"
        with output_file.open('a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(RawProduct.csv_headers())
            for product in products:
                writer.writerow(product.to_csv_row())
        print(f"Saved {len(products)} products to {output_file}")