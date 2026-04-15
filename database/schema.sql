CREATE DATABASE IF NOT EXISTS psat_db;
USE psat_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE campaigns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_name VARCHAR(150) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE email_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT,
    user_id INT,
    sent_time DATETIME,
    status VARCHAR(50),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE click_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT,
    user_id INT,
    click_time DATETIME,
    ip_address VARCHAR(100),
    user_agent TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE login_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT,
    user_id INT,
    attempt_time DATETIME,
    ip_address VARCHAR(100),
    user_agent TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);