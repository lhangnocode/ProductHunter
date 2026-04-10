import type { PlasmoCSConfig, PlasmoGetStyle } from "plasmo"
import { useEffect, useState, useRef } from "react"
import styleText from "data-text:./style.css"
import { findProductName, findProductPrice, cleanNameForSearch } from "./extractor"

export const config: PlasmoCSConfig = {
  matches: [
    "https://*.lazada.vn/*",
    "https://*.shopee.vn/*",
    "https://*.tiki.vn/*",
    "https://*.fptshop.com.vn/*",
    "https://cellphones.com.vn/*",
    "https://phongvu.vn/*",
    "https://*.tiktok.com/*",
    "https://*.alibaba.com/*"
  ],
  run_at: "document_idle"
}

export const getStyle: PlasmoGetStyle = () => {
  const style = document.createElement("style")
  style.textContent = styleText
  return style
}

const ProductCompareOverlay = () => {
  // Chỉ lưu name và price
  const [productInfo, setProductInfo] = useState({ name: "", price: 0 })
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any[]>([])
  
  const lastUrlRef = useRef(window.location.href)
  const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL

  useEffect(() => {
    const checkChange = () => {
      const currentUrl = window.location.href
      const newName = findProductName()
      const newPrice = findProductPrice()

      // Nếu chuyển trang (URL khác) hoặc tên sản phẩm trên màn hình thay đổi
      if (currentUrl !== lastUrlRef.current || (newName && newName !== productInfo.name)) {
        console.log("🔄 Cập nhật sản phẩm mới:", newName)
        lastUrlRef.current = currentUrl
        
        setProductInfo({
          name: newName || "",
          price: newPrice
        })

        // Reset dữ liệu cũ
        setResults([])
        setIsOpen(false)
      }
    }

    const interval = setInterval(checkChange, 2000)
    return () => clearInterval(interval)
  }, [productInfo.name])

  const handleFetchCompare = async () => {
    if (!productInfo.name) return
    if (isOpen) { setIsOpen(false); return; }

    setIsOpen(true)
    setLoading(true)

    try {
      const query = cleanNameForSearch(productInfo.name)
      const response = await fetch(`${API_BASE_URL}/products/compare?q=${encodeURIComponent(query)}`)
      const data = await response.json()
      setResults(data.data || [])
    } catch (error) {
      console.error("❌ Lỗi gọi API:", error)
    } finally {
      setLoading(false)
    }
  }

  if (!productInfo.name) return null


  return (
    <div className="fixed bottom-10 right-10 z-[2147483647] font-sans">
      <button
        onClick={handleFetchCompare}
        className="flex items-center gap-2 bg-[#ff4d2d] hover:bg-black text-white px-6 py-3 rounded-full shadow-xl transition-all border-none cursor-pointer font-bold"
      >
        <span>🔍</span>
        {loading ? "Đang tìm..." : "So sánh giá"}
      </button>

      {isOpen && (
        <div className="absolute bottom-16 right-0 w-[400px] bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-orange-500 to-red-600 text-white flex justify-between items-center">
            <h3 className="font-bold text-sm m-0">ProductHunter So Sánh</h3>
            <button onClick={() => setIsOpen(false)} className="text-white bg-transparent border-none cursor-pointer text-lg">✕</button>
          </div>

          {/* Results List */}
          <div className="overflow-y-auto p-4 space-y-4 bg-gray-50 max-h-[450px]">
            {loading ? (
              <div className="text-center py-20 text-gray-500 text-sm italic">Đang quét các sàn thương mại...</div>
            ) : results.length > 0 ? (
              results.map((group) => (
                <div key={group.id} className="bg-white p-3 rounded-xl border border-gray-200 shadow-sm hover:border-orange-300 transition-colors">
                  <div className="flex gap-3 mb-2">
                    <img src={group.main_image_url || "https://via.placeholder.com/150"} className="w-14 h-14 object-contain rounded" />
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-800 text-xs line-clamp-2">{group.normalized_name}</h4>
                      <p className="text-red-600 font-extrabold text-sm mt-1">{group.lowest_price?.toLocaleString()}₫</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2 border-t pt-2">
                    {group.platforms.map((p: any, idx: number) => (
                      <div key={idx} className="flex justify-between items-center text-[11px]">
                        <span className={`px-2 py-0.5 rounded font-bold ${p.platform_id === 7 ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
                          {p.platform_id === 7 ? 'FPT SHOP' : 'SÀN KHÁC'}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900">{p.current_price?.toLocaleString()}₫</span>
                          <a href={p.url} target="_blank" className="bg-gray-900 text-white px-3 py-1 rounded no-underline font-bold hover:bg-orange-600 transition-colors">XEM</a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-16 text-gray-400 text-sm">Không tìm thấy giá tốt hơn sàn này.</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ProductCompareOverlay