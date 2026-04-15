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
 * Hàm làm sạch tên sản phẩm:
 * 1. Loại bỏ cụm từ marketing (chính hãng, freeship...)
 * 2. Loại bỏ từ khóa danh mục dư thừa (điện thoại, laptop...)
 * 3. Làm sạch ký tự đặc biệt
 * 4. Lấy 6 từ khóa chất lượng nhất (thường là Brand + Model + Specs)
 */
export const cleanNameForSearch = (name: string): string => {
  if (!name) return ""

  // 1. Chuyển về chữ thường
  let cleaned = name.toLowerCase()

  // 2. Danh sách các cụm từ marketing/nhiễu cần xóa bỏ hoàn toàn
  const junkPhrases = [
    "chính hãng", "freeship", "trả góp", "ưu đãi", "giá rẻ", 
    "mới 100%", "fullbox", "quà tặng", "tặng kèm", "vn/a",
    "hot sale", "flash sale", "nhập khẩu", "giảm giá", "miễn phí",
    "lắp đặt", "hàng mới", "niêm yết"
  ]

  // Xóa các cụm từ này trước
  junkPhrases.forEach(phrase => {
    cleaned = cleaned.replace(new RegExp(phrase, 'g'), ' ')
  })

  // 3. Danh sách các từ đơn lẻ cần lọc bỏ (Stopwords)
  // Bao gồm cả loại sản phẩm nếu bạn muốn tìm kiếm tập trung vào Model/Brand
  const stopWords = new Set([
    "điện", "thoại", "máy", "tính", "bảng", "laptop", "tivi", "loại", 
    "chiếc", "cái", "hàng", "quà", "tặng", "kèm"
  ])

  return cleaned
    .replace(/[\[\]\(\)\-\|\/\+\*\!\&\%\#\@\.\,]/g, " ") // Xóa ký tự đặc biệt, dấu chấm, phẩy
    .split(/\s+/)                                       // Tách từ bằng khoảng trắng
    .filter(word => {
      const w = word.trim()
      return (
        w.length > 1 &&            // Bỏ từ 1 ký tự (a, à, s...)
        !stopWords.has(w) &&       // Bỏ từ trong blacklist
        !/^\d+$/.test(w)           // (Tùy chọn) Bỏ các từ chỉ có số đơn thuần nếu quá ngắn
      )
    })
    .slice(0, 7)                   // Tăng lên khoảng 7 từ để tránh mất thông số quan trọng (ví dụ RAM/ROM)
    .join(" ")
    .trim()
}