CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================
-- USERS
-- =========================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),

    -- 0 = FREE
    -- 1 = PREMIUM
    plan SMALLINT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- PRODUCTS
-- =========================
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    normalized_name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(255),
    main_image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- PLATFORMS
-- =========================
CREATE TABLE platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_url TEXT NOT NULL,
    affiliate_config TEXT
);

-- =========================
-- PLATFORM_PRODUCTS
-- =========================
CREATE TABLE platform_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL,
    platform_id INTEGER NOT NULL,

    raw_name TEXT,
    original_item_id VARCHAR(255),

    url TEXT NOT NULL,
    affiliate_url TEXT,

    current_price DECIMAL(12,2),
    original_price DECIMAL(12,2),

    rating DECIMAL(3,2) DEFAULT NULL, -- diem co the la 3.82
    reviews_count INTEGER DEFAULT 0,  -- so luot danh gia mac dinh la 0

    in_stock BOOLEAN DEFAULT TRUE,
    last_crawled_at TIMESTAMP,

    FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,

    FOREIGN KEY (platform_id)
        REFERENCES platforms(id)
        ON DELETE CASCADE,

    UNIQUE(platform_id, original_item_id)
);

-- =========================
-- PRICE_RECORDS
-- =========================
CREATE TABLE price_records (
    id BIGSERIAL PRIMARY KEY,
    platform_product_id UUID NOT NULL,

    price DECIMAL(12,2) NOT NULL,
    original_price DECIMAL(12,2),
    is_flash_sale BOOLEAN DEFAULT FALSE,

    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (platform_product_id)
        REFERENCES platform_products(id)
        ON DELETE CASCADE
);

-- =========================
-- WISH_LIST
-- =========================
CREATE TABLE wish_list (
    user_id UUID NOT NULL,
    product_id UUID NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, product_id),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE
);

-- =========================
-- PRICE_ALERTS
-- =========================
CREATE TABLE price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID NOT NULL,
    product_id UUID NOT NULL,

    target_price DECIMAL(12,2) NOT NULL,

    -- 0 = ACTIVE
    -- 1 = TRIGGERED
    status SMALLINT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,

    UNIQUE(user_id, product_id)
);

-- =========================
-- INDEXES
-- =========================

CREATE INDEX idx_platform_products_product
ON platform_products(product_id);

CREATE INDEX idx_platform_products_platform
ON platform_products(platform_id);

CREATE INDEX idx_price_records_platform_product
ON price_records(platform_product_id);

CREATE INDEX idx_price_records_recorded_at
ON price_records(recorded_at);

CREATE INDEX idx_price_alert_user
ON price_alerts(user_id);

CREATE INDEX idx_price_alert_product
ON price_alerts(product_id);
