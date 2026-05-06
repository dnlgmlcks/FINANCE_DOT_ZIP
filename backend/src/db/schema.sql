CREATE TABLE IF NOT EXISTS financials (
    id INT AUTO_INCREMENT PRIMARY KEY,

    stock_code VARCHAR(10) NOT NULL,
    year INT NOT NULL,

    standard_account VARCHAR(100) NOT NULL,
    thstrm_amount BIGINT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_ratios (
    id INT AUTO_INCREMENT PRIMARY KEY,

    stock_code VARCHAR(10) NOT NULL,
    year INT NOT NULL,

    ratio_name VARCHAR(100) NOT NULL,
    ratio_value DOUBLE,

    category VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warning_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,

    stock_code VARCHAR(10) NOT NULL,
    year INT NOT NULL,

    signal_type VARCHAR(50),
    severity VARCHAR(20),

    signal_name VARCHAR(100),
    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,

    stock_code VARCHAR(10) NOT NULL UNIQUE,
    corp_code VARCHAR(20),
    company_name VARCHAR(100) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS company_aliases (
    id INT AUTO_INCREMENT PRIMARY KEY,

    stock_code VARCHAR(10) NOT NULL,
    alias_name VARCHAR(100) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);