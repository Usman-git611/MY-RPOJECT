CREATE DATABASE IF NOT EXISTS hostelfix;
USE hostelfix;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'admin', 'staff') NOT NULL DEFAULT 'student',
    hostel VARCHAR(80),
    room_no VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(180) NOT NULL,
    category VARCHAR(80) NOT NULL,
    description TEXT NOT NULL,
    priority ENUM('Low', 'Medium', 'High', 'Urgent') DEFAULT 'Medium',
    image_filename VARCHAR(255),
    status ENUM('Pending', 'In Progress', 'Resolved') NOT NULL DEFAULT 'Pending',
    assigned_to INT,
    admin_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
);

INSERT INTO users (name, email, password_hash, role, hostel, room_no)
SELECT 'Hostel Admin', 'admin@hostelfix.com',
       'pbkdf2:sha256:100000$hostelfix$a5e43a0f33ddb0ce47a3da181e943f4eec12de065af93d2bbe42e056400a6f96',
       'admin', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@hostelfix.com');

INSERT INTO users (name, email, password_hash, role, hostel, room_no)
SELECT 'Maintenance Staff', 'staff@hostelfix.com',
       'pbkdf2:sha256:100000$hostelfix$a5e43a0f33ddb0ce47a3da181e943f4eec12de065af93d2bbe42e056400a6f96',
       'staff', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'staff@hostelfix.com');
