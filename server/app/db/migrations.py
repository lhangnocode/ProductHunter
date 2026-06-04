import logging

from sqlalchemy import text

from app.db.session import get_engine

logger = logging.getLogger(__name__)


async def run_startup_migrations() -> None:
    engine = get_engine()
    if engine.dialect.name != "postgresql":
        return

    async with engine.begin() as conn:
        for statement in _PLATFORM_PRODUCT_WISHLIST_ALERTS_SQL:
            await conn.execute(text(statement))

    logger.info("Database startup migrations completed")


_PLATFORM_PRODUCT_WISHLIST_ALERTS_SQL = [
"""
ALTER TABLE wish_list
ADD COLUMN IF NOT EXISTS platform_product_id UUID
""",
"""
ALTER TABLE price_alerts
ADD COLUMN IF NOT EXISTS platform_product_id UUID
""",
"""
WITH ranked_platform_products AS (
    SELECT
        id,
        product_id,
        ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY
                CASE WHEN current_price IS NULL THEN 1 ELSE 0 END,
                current_price ASC,
                id DESC
        ) AS rn
    FROM platform_products
)
UPDATE wish_list wl
SET platform_product_id = rpp.id
FROM ranked_platform_products rpp
WHERE wl.platform_product_id IS NULL
  AND wl.product_id = rpp.product_id
  AND rpp.rn = 1
""",
"""
WITH ranked_platform_products AS (
    SELECT
        id,
        product_id,
        ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY
                CASE WHEN current_price IS NULL THEN 1 ELSE 0 END,
                current_price ASC,
                id DESC
        ) AS rn
    FROM platform_products
)
UPDATE price_alerts pa
SET platform_product_id = rpp.id
FROM ranked_platform_products rpp
WHERE pa.platform_product_id IS NULL
  AND pa.product_id = rpp.product_id
  AND rpp.rn = 1
""",
"""
DELETE FROM wish_list
WHERE platform_product_id IS NULL
""",
"""
DELETE FROM price_alerts
WHERE platform_product_id IS NULL
""",
"""
ALTER TABLE wish_list
ALTER COLUMN platform_product_id SET NOT NULL
""",
"""
ALTER TABLE price_alerts
ALTER COLUMN platform_product_id SET NOT NULL
""",
"""
DO $$
DECLARE
    constraint_name text;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'wish_list'::regclass
      AND contype = 'p'
      AND conkey = ARRAY[
          (SELECT attnum FROM pg_attribute WHERE attrelid = 'wish_list'::regclass AND attname = 'user_id'),
          (SELECT attnum FROM pg_attribute WHERE attrelid = 'wish_list'::regclass AND attname = 'product_id')
      ]::smallint[];

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE wish_list DROP CONSTRAINT %I', constraint_name);
    END IF;
END $$
""",
"""
DO $$
DECLARE
    constraint_name text;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'wish_list'::regclass
      AND contype IN ('u', 'p')
      AND conkey = ARRAY[
          (SELECT attnum FROM pg_attribute WHERE attrelid = 'wish_list'::regclass AND attname = 'user_id'),
          (SELECT attnum FROM pg_attribute WHERE attrelid = 'wish_list'::regclass AND attname = 'platform_product_id')
      ]::smallint[];

    IF constraint_name IS NULL THEN
        ALTER TABLE wish_list
        ADD CONSTRAINT uq_user_platform_product_wishlist UNIQUE (user_id, platform_product_id);
    END IF;
END $$
""",
"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'wish_list'::regclass
          AND conname = 'fk_wish_list_platform_product'
    ) THEN
        ALTER TABLE wish_list
        ADD CONSTRAINT fk_wish_list_platform_product
        FOREIGN KEY (platform_product_id)
        REFERENCES platform_products(id)
        ON DELETE CASCADE;
    END IF;
END $$
""",
"""
DO $$
DECLARE
    constraint_name text;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'price_alerts'::regclass
      AND contype = 'u'
      AND conkey = ARRAY[
          (SELECT attnum FROM pg_attribute WHERE attrelid = 'price_alerts'::regclass AND attname = 'user_id'),
          (SELECT attnum FROM pg_attribute WHERE attrelid = 'price_alerts'::regclass AND attname = 'product_id')
      ]::smallint[];

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE price_alerts DROP CONSTRAINT %I', constraint_name);
    END IF;
END $$
""",
"""
DO $$
DECLARE
    constraint_name text;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'price_alerts'::regclass
      AND contype = 'u'
      AND conkey = ARRAY[
          (SELECT attnum FROM pg_attribute WHERE attrelid = 'price_alerts'::regclass AND attname = 'user_id'),
          (SELECT attnum FROM pg_attribute WHERE attrelid = 'price_alerts'::regclass AND attname = 'platform_product_id')
      ]::smallint[];

    IF constraint_name IS NULL THEN
        ALTER TABLE price_alerts
        ADD CONSTRAINT uq_user_platform_product_price_alert UNIQUE (user_id, platform_product_id);
    END IF;
END $$
""",
"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'price_alerts'::regclass
          AND conname = 'fk_price_alerts_platform_product'
    ) THEN
        ALTER TABLE price_alerts
        ADD CONSTRAINT fk_price_alerts_platform_product
        FOREIGN KEY (platform_product_id)
        REFERENCES platform_products(id)
        ON DELETE CASCADE;
    END IF;
END $$
""",
"""
CREATE INDEX IF NOT EXISTS idx_wish_list_platform_product
ON wish_list(platform_product_id)
""",
"""
CREATE INDEX IF NOT EXISTS idx_price_alert_platform_product
ON price_alerts(platform_product_id)
""",
]
