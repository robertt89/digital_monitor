-- Schema for LED display monitoring database
CREATE DATABASE IF NOT EXISTS monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE monitor;

-- Tabla principal del sistema de control
CREATE TABLE IF NOT EXISTS control_system (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id VARCHAR(64) NOT NULL UNIQUE,
    com_port VARCHAR(20) NOT NULL,
    global_brightness TINYINT UNSIGNED,
    screen_count INT,
    sender_count INT,
    is_initialized BOOLEAN DEFAULT FALSE,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_control_com_port (com_port)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de tarjetas enviadoras (sending cards)
CREATE TABLE IF NOT EXISTS sending_card (
    id INT PRIMARY KEY AUTO_INCREMENT,
    control_system_id INT NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    sender_index TINYINT UNSIGNED NOT NULL,
    dvi_status BOOLEAN,
    is_video_ok BOOLEAN,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (control_system_id) REFERENCES control_system(id) ON DELETE CASCADE,
    UNIQUE KEY unique_sender (control_system_id, sender_index),
    INDEX idx_sending_device (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de tarjetas receptoras (receiving cards/scan boards)
CREATE TABLE IF NOT EXISTS scan_board (
    id INT PRIMARY KEY AUTO_INCREMENT,
    control_system_id INT NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    sender_index TINYINT UNSIGNED NOT NULL,
    port_index TINYINT UNSIGNED NOT NULL,
    scan_board_index SMALLINT UNSIGNED NOT NULL,
    status ENUM('OK', 'Error', 'Unknown') DEFAULT 'Unknown',
    temperature FLOAT,
    voltage FLOAT,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (control_system_id) REFERENCES control_system(id) ON DELETE CASCADE,
    UNIQUE KEY unique_scan_board (control_system_id, sender_index, port_index, scan_board_index),
    INDEX idx_status (status),
    INDEX idx_scan_device (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Vista resumen del sistema
CREATE OR REPLACE VIEW v_system_status AS
SELECT 
    cs.id,
    cs.device_id,
    cs.com_port,
    cs.global_brightness,
    cs.is_initialized,
    cs.last_update,
    COUNT(DISTINCT sc.id) as total_sending_cards,
    COUNT(DISTINCT sb.id) as total_scan_boards,
    SUM(CASE WHEN sb.status = 'OK' THEN 1 ELSE 0 END) as scan_boards_ok,
    SUM(CASE WHEN sb.status = 'Error' THEN 1 ELSE 0 END) as scan_boards_error,
    AVG(sb.temperature) as avg_temperature,
    MAX(sb.temperature) as max_temperature
FROM control_system cs
LEFT JOIN sending_card sc ON cs.id = sc.control_system_id
LEFT JOIN scan_board sb ON cs.id = sb.control_system_id
GROUP BY cs.id, cs.device_id, cs.com_port, cs.global_brightness, cs.is_initialized, cs.last_update;
