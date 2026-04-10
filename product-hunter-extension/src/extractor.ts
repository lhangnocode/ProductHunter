/**
 * Cấu hình selector riêng biệt cho từng sàn
 */
const PLATFORM_CONFIG = {
  shopee: {
    name: [".vR6K3w", "h1[role='main']", "h1"],
    price: [".IZPeQz", ".B67UQ0", "._44qnta"],
  },
  lazada: {
    name: [".pdp-mod-product-badge-title-v2", ".pdp-product-title"],
    price: [".pdp-v2-product-price-content-salePrice-amount", ".pdp-price_type_normal"],
  },
  tiki: {
    name: [
      "h1[data-view-id='pdp_details_title']", 
      "h1.dEurho", 
      "main h1", 
      "h1"
    ],
    price: [
      ".product-price__current-price",
      ".product-price__current",
      "div[class*='current-price']"
    ],
  },
  fptshop: {
    name: ["h1.pc\\:l6-semibold", "h1", ".st-name"],
    price: [".h4-bold", ".text-red-red-7", ".st-price-main"],
  },
  cellphones: {
    name: [".box-product-name h1", "h1"],
    price: [".box-product-price .sale-price", ".sale-price"],
  },
  phongvu: {
    name: ["h1.css-nlaxuc", "h1", ".product-name"],
    price: [".att-product-detail-latest-price", ".css-roachw", "div[type='title']"],
  },
  tiktok: {
    name: ["h1 span", "h1", ".product-name"],
    price: [".Headline-Semibold", "span[style*='font-size:36px']", ".price"],
  },
  alibaba: {
    name: [".module_title h1", "h1", "h1[title]"],
    price: [".module_price .id-text-2xl", "div[data-testid='range-price'] span", ".id-text-2xl"],
  },
  // Mặc định cho các trang không xác định
  default: {
    name: ["h1", "title"],
    price: [".price", "#price"]
  }
}

/**
 * Hàm xác định xem đang ở sàn nào dựa vào URL
 */
const getCurrentPlatform = () => {
  const host = window.location.hostname
  if (host.includes("shopee.vn")) return "shopee"
  if (host.includes("lazada.vn")) return "lazada"
  if (host.includes("tiki.vn")) return "tiki"
  if (host.includes("fptshop.com.vn")) return "fptshop"
  if (host.includes("cellphones.com.vn")) return "cellphones"
  if (host.includes("phongvu.vn")) return "phongvu";
  if (host.includes("tiktok.com")) return "tiktok";
  if (host.includes("alibaba.com")) return "alibaba";
  return "default"
}

/**
 * Hàm tìm tên sản phẩm
 */
export const findProductName = (): string | null => {
  const platform = getCurrentPlatform()
  const selectors = PLATFORM_CONFIG[platform].name

  for (const s of selectors) {
    const el = document.querySelector(s) as HTMLElement
    if (el && el.innerText.trim()) {
      return el.innerText.trim()
    }
  }
  return null
}

/**
 * Hàm lấy giá sản phẩm hiện tại
 */
export const findProductPrice = (): number => {
  const platform = getCurrentPlatform()
  const selectors = PLATFORM_CONFIG[platform].price

  for (const s of selectors) {
    const el = document.querySelector(s) as HTMLElement
    if (el) {
      // Xóa tất cả ký tự không phải số (ví dụ "5.000.000đ" -> "5000000")
      const priceText = el.innerText.replace(/\D/g, "")
      return parseInt(priceText) || 0
    }
  }
  return 0
}

/**
 * Hàm làm sạch tên sản phẩm để search API (giữ lại 6 từ đầu)
 */
export const cleanNameForSearch = (name: string): string => {
  if (!name) return ""
  return name
    .replace(/[\[\]\(\)\-\|]/g, " ") // Thay thế ký tự đặc biệt bằng khoảng trắng
    .split(/\s+/)                   // Tách từ bằng khoảng trắng
    .filter(word => word.length > 1) // Loại bỏ các từ đơn lẻ (ví dụ: "a", "à")
    .slice(0, 6)                    // Lấy 6 từ đầu tiên
    .join(" ")
}