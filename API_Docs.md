# Tai lieu API - Product Hunter

Tai lieu nay thong ke cac endpoint dang duoc khai bao trong FastAPI server.

- API prefix: `/api/v1`
- Bearer auth: gui header `Authorization: Bearer <access_token>`
- Crawler auth: gui header `X-API-Key` khop voi `DEV_API_KEY`
- FastAPI OpenAPI UI mac dinh: `/docs`

## 1. System

Hai endpoint nay khong dung prefix `/api/v1`.

| Endpoint | Method | Tac dung |
| :--- | :---: | :--- |
| `/` | `GET` | Tra thong tin chao mung va version API. |
| `/health` | `GET` | Health check cua API. |

## 2. Authentication & User (`/api/v1/auth`)

| Endpoint | Method | Input chinh | Auth | Ham xu ly |
| :--- | :---: | :--- | :---: | :--- |
| `/auth/register` | `POST` | JSON: `email`, `password`, optional `full_name` | No | `register` |
| `/auth/login` | `POST` | OAuth2 form: `username`, `password` | No | `login` |
| `/auth/me` | `GET` | - | Bearer | `get_my_profile` |
| `/auth/premium-feature` | `POST` | - | Premium Bearer | `use_premium_feature` |
| `/auth/refresh` | `POST` | JSON: `refresh_token` | No | `refresh_access_token` |
| `/auth/forgot-password` | `POST` | JSON: `email` | No | `forgot_password` |
| `/auth/reset-password` | `POST` | JSON: `token`, `new_password` | No | `reset_password` |
| `/auth/{provider}/login` | `GET` | Query: optional `frontend_url` | No | `social_login` |
| `/auth/{provider}/callback` | `GET` | OAuth callback query from provider | No | `social_callback` |

Social auth hien chi ho tro `google` va `github`. Endpoint login tra redirect sang provider; callback tra redirect ve frontend kem token neu OAuth thanh cong.

## 3. Products (`/api/v1/products`)

| Endpoint | Method | Query chinh | Auth | Ham xu ly |
| :--- | :---: | :--- | :---: | :--- |
| `/products/search` | `GET` | `q` length >= 2, optional `page`, `limit` | No | `search_products_list` |
| `/products/` | `GET` | optional `skip`, `limit` | No | `get_all_products` |
| `/products/searchAll` | `GET` | `q` length >= 2, optional `page`, `limit` | No | `search_products_list` |
| `/products/compare` | `GET` | `q` length >= 2 | No | `search_and_compare_products` |
| `/products/compare2` | `GET` | `q` length >= 2 | No | `search_and_compare_mock` |

`/products/compare2` ket hop product trong DB voi mock platform data dang nam trong module API, nen phu hop cho luong dev/test hien tai hon la nguon so sanh production.

## 4. Crawler Ingest (`/api/v1/crawler`)

Tat ca endpoint trong group nay yeu cau `X-API-Key`.

| Endpoint | Method | Input chinh | Ham xu ly |
| :--- | :---: | :--- | :--- |
| `/crawler/products` | `POST` | JSON product ingest: `normalized_name`, `slug`, optional product fields | `upload_product` |
| `/crawler/platform-products` | `POST` | JSON array platform-product ingest | `upload_platform_products_bulk` |

Khi ingest platform product, server tao mot `price_records` entry moi cho gia tai thoi diem crawl.

## 5. Platforms (`/api/v1/platforms`)

| Endpoint | Method | Input chinh | Auth | Ham xu ly |
| :--- | :---: | :--- | :---: | :--- |
| `/platforms/` | `POST` | JSON: `name`, `base_url`, optional `affiliate_config` | No | `create_platform` |
| `/platforms/` | `GET` | - | No | `get_platforms` |

## 6. Platform Products (`/api/v1/platform_products`)

| Endpoint | Method | Query chinh | Auth | Ham xu ly |
| :--- | :---: | :--- | :---: | :--- |
| `/platform_products/platform-products/search` | `GET` | `name`, optional `page`, `limit` | No | `search_platform_products_endpoint` |
| `/platform_products/platform-products/by-product-id` | `GET` | `product_id`, optional `page`, `limit` | No | `get_platform_products_by_product_id_endpoint` |
| `/platform_products/platform-products` | `GET` | optional `offset`, `limit` | No | `get_all_platform_products` |
| `/platform_products/platform-products/trending` | `GET` | optional `limit` | No | `get_trending_platform_products` |

`limit` cua cac endpoint platform-product dang duoc validate trong khoang `1..100`.

## 7. Price Records (`/api/v1/price_record`)

| Endpoint | Method | Input chinh | Auth | Ham xu ly |
| :--- | :---: | :--- | :---: | :--- |
| `/price_record/price-records` | `GET` | Query: optional `offset`, `limit` | No | `get_all_price_records` |
| `/price_record/price-records/{platform_product_id}` | `GET` | Path UUID `platform_product_id` | No | `get_price_record_by_platform_product_id` |
| `/price_record/price-records` | `POST` | JSON price record payload | No | `push_price_record` |
| `/price_record/price-records/batch` | `POST` | JSON array price record payloads | No | `push_price_records_batch` |
| `/price_record/price-analysis/{platform_product_id}` | `GET` | Path UUID; query `current_price`, `original_price` | No | `get_price_analysis` |

Price-record create payload:

```json
{
  "platform_product_id": "uuid",
  "price": 28000000,
  "original_price": 34990000,
  "is_flash_sale": false,
  "recorded_at": "2026-04-01T10:00:00Z"
}
```

`original_price`, `is_flash_sale`, va `recorded_at` la optional. Batch create bo qua item co `platform_product_id` khong ton tai.

## 8. Price Alerts (`/api/v1/price_alerts`)

Tat ca endpoint trong group nay yeu cau Bearer auth.

| Endpoint | Method | Input chinh | Ham xu ly |
| :--- | :---: | :--- | :--- |
| `/price_alerts/` | `POST` | JSON: `platform_product_id` or `product_id`, plus `target_price` | `create_or_update_alert` |
| `/price_alerts/` | `GET` | - | `get_my_alerts` |
| `/price_alerts/{platform_product_id}` | `DELETE` | Path UUID `platform_product_id` | `delete_price_alert` |
| `/price_alerts/trigger` | `POST` | JSON: optional `product_id`, optional `platform_product_id` | `trigger_price_check` |

Create/update payload:

```json
{
  "platform_product_id": "uuid",
  "target_price": 25000000
}
```

`product_id` van duoc chap nhan de tu resolve sang mot platform product phu hop, nhung `platform_product_id` la cach ro rang hon vi alert hien theo doi dung offer tren tung san.

Response item:

```json
{
  "product_id": "uuid",
  "platform_product_id": "uuid",
  "target_price": 25000000,
  "status": 0,
  "product_name": "iPhone 15 Pro Max - Shopee",
  "main_image_url": "https://example.com/image.jpg",
  "current_price": 24990000
}
```

`status`: `0` la active, `1` la triggered. `/price_alerts/trigger` kiem tra alert cua user dang dang nhap. Body `{}` la hop le de check tat ca alert cua user; body co `product_id` hoac `platform_product_id` gioi han pham vi check.

## 9. Wish Lists (`/api/v1/wish_lists`)

Tat ca endpoint trong group nay yeu cau Bearer auth.

| Endpoint | Method | Input chinh | Ham xu ly |
| :--- | :---: | :--- | :--- |
| `/wish_lists/` | `POST` | JSON: `platform_product_id` or `product_id` | `create_wishlist_item` |
| `/wish_lists/` | `GET` | - | `get_my_wishlist` |
| `/wish_lists/{platform_product_id}` | `DELETE` | Path UUID `platform_product_id` | `delete_wishlist_item` |

Wishlist item response fields include `product_id`, `platform_product_id`, `added_at`, optional `product_name`, optional `main_image_url`, optional `current_price`, and optional `original_price`.

## 10. Device Tokens (`/api/v1/device_tokens`)

Tat ca endpoint trong group nay yeu cau Bearer auth. Mobile app dung group nay de dang ky FCM registration token cho push notification.

| Endpoint | Method | Input chinh | Ham xu ly |
| :--- | :---: | :--- | :--- |
| `/device_tokens/` | `POST` | JSON: `token`, optional `platform` default `android` | `register_device_token` |
| `/device_tokens/{token}` | `DELETE` | Path string `token` | `remove_device_token` |

Register/update payload:

```json
{
  "token": "fcm-registration-token",
  "platform": "android"
}
```

Register response:

```json
{
  "id": "uuid",
  "token": "fcm-registration-token",
  "platform": "android",
  "is_active": true,
  "created_at": "2026-06-05T10:00:00Z",
  "updated_at": "2026-06-05T10:00:00Z",
  "last_seen_at": "2026-06-05T10:00:00Z"
}
```

`POST` upsert theo token: neu token da ton tai thi cap nhat user, platform, danh dau active va refresh `last_seen_at`. `DELETE` chi deactivate token cua user dang dang nhap; user khac khong deactivate duoc token nay.

## 11. Advisor (`/api/v1/advisor`)

| Endpoint | Method | Input chinh | Auth | Ham xu ly |
| :--- | :---: | :--- | :---: | :--- |
| `/advisor/chat` | `POST` | JSON: `message`, optional `history`, optional `context` | No | `advisor_chat` |

Advisor tra ve `answer`, danh sach `recommendations`, va `sources`. Service co the tra
`503` neu thieu cau hinh provider, `502` neu provider loi, hoac `500` neu retrieval loi.

## 12. Agent (`/api/v1/agent`)

| Endpoint | Method | Input chinh | Auth | Ham xu ly |
| :--- | :---: | :--- | :---: | :--- |
| `/agent/chat` | `POST` | JSON: `message`, optional `history`, optional `context`, optional `include_tool_trace` | No | `agent_chat` |
| `/agent/chat/stream` | `POST` | Same payload as `/agent/chat` | No | `agent_chat_stream` |

Agent request payload:

```json
{
  "message": "Find me a good laptop deal",
  "history": [
    {
      "role": "user",
      "content": "I prefer ASUS"
    }
  ],
  "context": {
    "active_tab": "search",
    "search_query": "laptop",
    "product_id": "uuid",
    "shop_id": 1
  },
  "include_tool_trace": true
}
```

`/agent/chat` tra JSON gom `answer`, `recommendations`, `sources`, `tool_trace`, `handoff_required`, `alternatives`, `objection_answers`, `urgency_cues`, va optional `disclaimer`. `/agent/chat/stream` tra Server-Sent Events voi `media_type` la `text/event-stream`.

## 13. Payments (`/api/v1/payments`)

Endpoint nay yeu cau Bearer auth.

| Endpoint | Method | Input chinh | Ham xu ly |
| :--- | :---: | :--- | :--- |
| `/payments/request` | `POST` | Multipart form: `amount`, file `receipt` | `create_payment_request` |

Server luu receipt vao `static/receipts` va tao `payment_requests` row voi `status = 0` pending.

## 14. Admin (`/api/v1/admin`)

Tat ca endpoint trong group nay yeu cau Bearer auth cua user nam trong danh sach admin server-side.

| Endpoint | Method | Input chinh | Ham xu ly |
| :--- | :---: | :--- | :--- |
| `/admin/overview` | `GET` | - | `get_admin_overview` |
| `/admin/users` | `GET` | - | `list_users` |
| `/admin/users/{user_id}/plan` | `PATCH` | JSON: `plan` (`0` or `1`) | `update_user_plan` |
| `/admin/payments` | `GET` | - | `list_payments` |
| `/admin/payments/{payment_id}/approve` | `POST` | Path UUID `payment_id` | `approve_payment` |
| `/admin/payments/{payment_id}/reject` | `POST` | Path UUID `payment_id` | `reject_payment` |

Admin overview tra ve counts, recent products va sample offers. Payment approval set payment `status = 1` va nang user len plan premium (`plan = 1`); reject set `status = 2`.
