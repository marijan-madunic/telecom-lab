CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    data_limit_mb INT NOT NULL,
    qos_profile VARCHAR(50) NOT NULL
);

CREATE TABLE subscribers (
    id SERIAL PRIMARY KEY,
    imsi VARCHAR(20) UNIQUE NOT NULL,
    msisdn VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    plan_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_subscribers_plan
        FOREIGN KEY (plan_id) REFERENCES plans(id),
    CONSTRAINT chk_subscriber_status
        CHECK (status IN ('ACTIVE', 'SUSPENDED', 'BARRED'))
);

CREATE TABLE subscriber_profiles (
    subscriber_id INT PRIMARY KEY,
    access_restriction BOOLEAN DEFAULT FALSE,
    roaming_enabled BOOLEAN DEFAULT TRUE,
    max_sessions INT DEFAULT 3,
    CONSTRAINT fk_profiles_subscriber
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
    CONSTRAINT chk_max_sessions
        CHECK (max_sessions >= 0)
);

CREATE TABLE balances (
    subscriber_id INT PRIMARY KEY,
    remaining_data_mb INT NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_balances_subscriber
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
    CONSTRAINT chk_remaining_data
        CHECK (remaining_data_mb >= 0)
);

CREATE TABLE usage_records (
    id SERIAL PRIMARY KEY,
    subscriber_id INT NOT NULL,
    used_mb INT NOT NULL,
    session_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_usage_subscriber
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
    CONSTRAINT chk_used_mb
        CHECK (used_mb > 0)
);

CREATE INDEX idx_imsi ON subscribers(imsi);
CREATE INDEX idx_usage_subscriber_id ON usage_records(subscriber_id);
CREATE INDEX idx_usage_session_id ON usage_records(session_id);
