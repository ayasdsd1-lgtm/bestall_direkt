-- ============================================================
-- bestall_direkt – Databasschema
-- Genererat från Supabase (PostgreSQL)
-- ============================================================

-- Tabell: company_owner
CREATE TABLE IF NOT EXISTS company_owner (
    company_id          INT4        PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    company_name        VARCHAR,
    email               VARCHAR     UNIQUE,
    password            VARCHAR,
    personal_identity_number TEXT   UNIQUE,
    phone               TEXT,
    blocked             BOOLEAN,
    is_active           BOOLEAN
);

-- Tabell: company_business
CREATE TABLE IF NOT EXISTS company_business (
    company_business_id INT4        PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    company_name        VARCHAR     NOT NULL,
    description         TEXT,
    phone               BPCHAR,
    company_id          INT4        REFERENCES company_owner(company_id),
    address             TEXT,
    category            TEXT,
    logo_url            TEXT,
    email               TEXT
);

-- Tabell: customer
CREATE TABLE IF NOT EXISTS customer (
    customer_id         INT4        PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name                VARCHAR     NOT NULL,
    email               VARCHAR,
    phone               VARCHAR
);

-- Tabell: menu_item
CREATE TABLE IF NOT EXISTS menu_item (
    menu_item_id        INT4        PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    item_name           VARCHAR     NOT NULL,
    price               NUMERIC     NOT NULL,
    company_business_id INT4        REFERENCES company_business(company_business_id),
    description         TEXT,
    image_url           TEXT
);

-- Tabell: orders
CREATE TABLE IF NOT EXISTS orders (
    order_id            INT4        PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    date                TIMESTAMP,
    status              VARCHAR,
    customer_id         INT4        REFERENCES customer(customer_id),
    company_business_id INT4        REFERENCES company_business(company_business_id)
);

-- Tabell: order_item
CREATE TABLE IF NOT EXISTS order_item (
    order_id            INT4        NOT NULL REFERENCES orders(order_id),
    menu_item_id        INT4        NOT NULL REFERENCES menu_item(menu_item_id),
    amount              INT4,
    PRIMARY KEY (order_id, menu_item_id)
);
