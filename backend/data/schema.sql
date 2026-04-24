CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cost_price TEXT NOT NULL DEFAULT '0.00',
    recommended_price TEXT NOT NULL DEFAULT '0.00',
    sale_price TEXT NOT NULL DEFAULT '0.00'
);

CREATE TABLE IF NOT EXISTS costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amount TEXT NOT NULL,
    cost_type TEXT NOT NULL CHECK(cost_type IN ('fixed', 'variable')),
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product_variable_costs (
    product_id INTEGER NOT NULL,
    cost_id INTEGER NOT NULL,
    PRIMARY KEY (product_id, cost_id),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_id) REFERENCES costs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    sale_price TEXT NOT NULL,
    sale_date TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS sale_variable_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    cost_id INTEGER NOT NULL,
    cost_name TEXT NOT NULL,
    amount TEXT NOT NULL,
    sale_date TEXT NOT NULL,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_id) REFERENCES costs(id)
);
