CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    mobile VARCHAR(15),
    dob DATE,
    address VARCHAR(255),
    state VARCHAR(100),
    zipcode VARCHAR(10),
    pin VARCHAR(10),
    device_fingerprint VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS merchants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    upi VARCHAR(50),
    category VARCHAR(50),
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_mobile VARCHAR(15),
    merchant_upi VARCHAR(50),
    amount FLOAT,
    status VARCHAR(20),
    date_time DATETIME,
    category VARCHAR(50),
    age INT,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7)
);

-- Default admin (password: admin123)
INSERT INTO admin (username, password) VALUES ('admin', MD5('admin123'));

-- Sample users
INSERT INTO users (name, email, mobile, dob, address, state, zipcode) VALUES
('Shaily Gajavelli', 'shailygajavelli5@gmail.com', '9999999999', '1998-05-15', '123 Main St', 'Telangana', '500001'),
('Deekshitha', 'deeki463@gmail.com', '7702777044', '2004-05-18', 'narapally', 'Telangana', '500088'),
('Deekshitha N', 'deeki463@gmail.com', '7702777777', '2008-05-18', 'medchal', 'Telangana', '500088'),
('Kavya E', 'kavyaemmidi156@gmail.com', '7993763230', '2005-06-06', 'hyderabad', 'Telangana', '500065'),
('Test User', 'testuser@gmail.com', '8888888888', '2000-01-01', '456 Park Ave', 'Karnataka', '560001');

-- Run these ALTER statements if the database already exists (to add missing columns):
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS pin VARCHAR(10);
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(100);
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
-- ALTER TABLE transactions ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,7);
-- ALTER TABLE transactions ADD COLUMN IF NOT EXISTS longitude DECIMAL(10,7);
