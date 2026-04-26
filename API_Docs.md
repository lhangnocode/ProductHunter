# Tài liệu thống kê API - Product Hunter

Dưới đây là danh sách tổng hợp các API của dự án Product Hunter, được chia theo từng module chức năng:

## 1. Authentication & User (`/auth`)
Các API quản lý việc xác thực, người dùng và OAuth.

| Endpoint | Method | Tác dụng | Hàm xử lý |
| :--- | :---: | :--- | :--- |
| `/auth/register` | `POST` | Đăng ký tài khoản người dùng mới. | `register` |
| `/auth/login` | `POST` | Đăng nhập tài khoản. | `login` |
| `/auth/me` | `GET` | Lấy thông tin cá nhân của người dùng đang đăng nhập. | `get_my_profile` |
| `/auth/premium-feature` | `POST` | Sử dụng tính năng nâng cao (Premium). | `use_premium_feature` |
| `/auth/refresh` | `POST` | Cấp lại Refresh/Access Token. | `refresh_access_token` |
| `/auth/{provider}/login` | `GET` | Đăng nhập thông qua mạng xã hội (Google, Facebook...). | `social_login` |
| `/auth/{provider}/callback` | `GET` | API callback xác nhận trạng thái sau khi login mạng xã hội. | `social_callback` |

## 2. Products (`/products`)
Các API liên quan đến các sản phẩm chung được thống nhất từ nhiều nguồn.

| Endpoint | Method | Tác dụng | Hàm xử lý |
| :--- | :---: | :--- | :--- |
| `/products/search` | `GET` | Tìm kiếm sản phẩm theo từ khóa (hỗ trợ phân trang). | `search_products_list` |
| `/products/searchAll` | `GET` | Truy xuất và tìm kiếm toàn bộ danh mục sản phẩm. | `search_products_list` (searchAll) |
| `/products/` | `GET` | Lấy danh sách sản phẩm. | `get_all_products` |
| `/products/compare` | `GET` | Tìm kiếm và so sánh chi tiết các sản phẩm từ các sàn. | `search_and_compare_products` |
| `/products/compare2` | `GET` | API so sánh sản phẩm theo mock data (có thể dùng trong môi trường test/dev). | `search_and_compare_mock` |

## 3. Crawler (`/crawler`)
Các API nội bộ dùng cho hệ thống lấy dữ liệu tự động (Cron job/Crawler bots).

| Endpoint | Method | Tác dụng | Hàm xử lý |
| :--- | :---: | :--- | :--- |
| `/crawler/` | `POST` | Upload dữ liệu một sản phẩm đơn lẻ từ trang thương mại điện tử vào CSDL. | `upload_product` |
| `/crawler/bulk` | `POST` | Tải lên dữ liệu hàng loạt các sản phẩm sau khi crawl hoàn thành. | `upload_platform_products_bulk` |

## 4. Platform Products (`/platform_products`)
Các API trích xuất chi tiết sản phẩm cụ thể thuộc về từng Sàn thương mại điện tử (Shopee, Tiki, Lazada...).

| Endpoint | Method | Tác dụng | Hàm xử lý |
| :--- | :---: | :--- | :--- |
| `/platform_products/` | `GET` | Lấy thông tin sản phẩm trên sàn thông qua các query filters. | `search_platform_products_endpoint`, `get_platform_products_by_product_id_endpoint`, `get_all_platform_products` |
| `/platform_products/trending` | `GET` | Lấy chi tiết các sản phẩm đang phổ biến/xu hướng trên các sàn. | `get_trending_platform_products` |

## 5. Platforms (`/platforms`)
Các API quản lý danh sách sàn thương mại điện tử.

| Endpoint | Method | Tác dụng | Hàm xử lý |
| :--- | :---: | :--- | :--- |
| `/platforms/` | `POST` | Thêm mới thông tin một sàn giao dịch TMĐT. | `create_platform` |
| `/platforms/` | `GET` | Lấy toàn bộ danh sách các nền tảng (Platform) được hỗ trợ. | `get_platforms` |

## 6. Price Record (`/price_record`)
Các API liên quan đến lịch sử thay đổi giá của sản phẩm.

| Endpoint | Method | Tác dụng | Hàm xử lý |
| :--- | :---: | :--- | :--- |
| `/price_record/` | `GET` | Lấy danh sách các bản ghi giá trị theo thời gian. Có thể lọc theo ID sản phẩm trên sàn. | `get_all_price_records`, `get_price_record_by_platform_product_id` |
| `/price_record/` | `POST` | Lưu trữ lại 1 mốc thay đổi giá cho sản phẩm trên sàn. | `push_price_record` |
| `/price_record/batch` | `POST` | Cập nhật đồng loạt (Batch) một danh sách các mốc thay đổi giá. | `push_price_records_batch` |
| `/price_record/price-analysis/{platform_product_id}` | `GET` | Phân tích xu hướng giá của bản ghi sản phẩm với ID liên kết tương ứng. | `get_price_analysis` |

## 7. Price Alerts (`/price_alerts`)
Chức năng tự động thông báo giá theo yêu cầu từ User.

| Endpoint | Method | Tác dụng | Hàm xử lý |
| :--- | :---: | :--- | :--- |
| `/price_alerts/` | `POST` | Cài đặt thông báo tự động (báo giá/mục tiêu) cho người dùng. | `create_or_update_alert` |
| `/price_alerts/` | `GET` | Lấy danh sách những thông báo giá mà người dùng hiện tại đang cài đặt. | `get_my_alerts` |
| `/price_alerts/{product_id}` | `DELETE` | Hủy bỏ thông báo giá đã cài đặt theo mã Sản phẩm. | `delete_price_alert` |
| `/price_alerts/trigger` | `POST` | Kích hoạt bộ kiểm tra ngầm, lọc lại giá và thông báo nếu có alert thoả mãn điều kiện. | `trigger_price_check` |

## 8. Wish Lists (`/wish_lists`)
Quản lý danh mục Sản phẩm Yêu thích.

| Endpoint | Method | Tác dụng | Hàm xử lý |
| :--- | :---: | :--- | :--- |
| `/wish_lists/` | `POST` | Thêm 1 sản phẩm vào trang đánh dấu yêu thích. | `create_wishlist_item` |
| `/wish_lists/` | `GET` | Hiển thị tất cả danh mục mong muốn của cá nhân người dùng. | `get_my_wishlist` |
| `/wish_lists/{product_id}` | `DELETE` | Loại bỏ 1 món hàng ra khỏi danh sách mong muốn. | `delete_wishlist_item` |