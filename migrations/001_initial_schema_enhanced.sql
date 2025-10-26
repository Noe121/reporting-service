-- NILBX Reporting Service Database Schema
-- Database: reporting_db (Port 3324) - LOCAL DEVELOPMENT ONLY
-- Cloud/Production: Uses nilbx_db (shared database)
-- Purpose: Report generation, scheduling, and analytics

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS reporting_db CHARACTER SET utf8mb4 COLLATE=utf8mb4_unicode_ci;
USE reporting_db;

-- Create user with access from any host (for Docker containers)
CREATE USER IF NOT EXISTS 'reportinguser'@'%' IDENTIFIED BY 'reportingpass';
GRANT ALL PRIVILEGES ON reporting_db.* TO 'reportinguser'@'%';
FLUSH PRIVILEGES;

-- ====================================
-- Core Tables from ENHANCED Schema
-- (Minimal reference tables for development)
-- ====================================

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    role ENUM('athlete', 'sponsor', 'fan', 'admin') NOT NULL DEFAULT 'fan',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_email (email),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='User reference table - synced from auth_db in production';

-- ====================================
-- Report Templates
-- ====================================
CREATE TABLE IF NOT EXISTS report_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    template_type VARCHAR(50) NOT NULL,
    description TEXT,
    sections JSON COMMENT 'Report sections configuration',
    export_formats JSON COMMENT 'Supported export formats',
    parameters JSON COMMENT 'Template parameters',
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME NULL,

    INDEX idx_type_active (template_type, is_active),
    INDEX idx_template_name (template_name),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Report template definitions';

-- ====================================
-- Reports
-- ====================================
CREATE TABLE IF NOT EXISTS reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    template_id INT NOT NULL,
    report_name VARCHAR(100) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    date_range_start DATETIME NOT NULL,
    date_range_end DATETIME NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    progress_percent INT DEFAULT 0,
    rows_generated INT DEFAULT 0,
    total_records INT,
    generated_at DATETIME NULL,
    generation_time_seconds DECIMAL(10, 2),
    file_path VARCHAR(500),
    file_size INT,
    error_message TEXT,
    filters JSON COMMENT 'Applied filters',
    generated_by VARCHAR(50) DEFAULT 'manual',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES report_templates(id),

    INDEX idx_user_status (user_id, status),
    INDEX idx_type_created (report_type, created_at),
    INDEX idx_generated_status (generated_at, status),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Generated reports';

-- ====================================
-- Report Schedules
-- ====================================
CREATE TABLE IF NOT EXISTS report_schedules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    template_id INT NOT NULL,
    schedule_name VARCHAR(100) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    time_of_day VARCHAR(10) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    recipients JSON COMMENT 'Email recipients list',
    delivery_method VARCHAR(50) DEFAULT 'email',
    is_enabled BOOLEAN DEFAULT TRUE,
    next_run_at DATETIME,
    last_run_at DATETIME NULL,
    run_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES report_templates(id),

    INDEX idx_user_enabled (user_id, is_enabled),
    INDEX idx_next_run (next_run_at),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Scheduled report generation';

-- ====================================
-- Report Exports
-- ====================================
CREATE TABLE IF NOT EXISTS report_exports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    export_format VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT,
    file_hash VARCHAR(128),
    export_status VARCHAR(50) DEFAULT 'pending',
    exported_at DATETIME NULL,
    download_count INT DEFAULT 0,
    last_downloaded_at DATETIME NULL,
    error_message TEXT,
    compression VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME NULL,

    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,

    INDEX idx_report_format (report_id, export_format),
    INDEX idx_status (export_status),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Report export files';

-- ====================================
-- Report Metrics
-- ====================================
CREATE TABLE IF NOT EXISTS report_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4) NOT NULL,
    metric_unit VARCHAR(50) NOT NULL,
    metric_category VARCHAR(50) DEFAULT 'performance',
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME NULL,

    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,

    INDEX idx_report_name (report_id, metric_name),
    INDEX idx_category (metric_category),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Report performance metrics';

-- ====================================
-- Report Access Logs
-- ====================================
CREATE TABLE IF NOT EXISTS report_access_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    user_id INT NOT NULL,
    access_type VARCHAR(50) NOT NULL,
    access_status VARCHAR(50) DEFAULT 'success',
    ip_address VARCHAR(45),
    user_agent TEXT,
    access_duration_seconds INT,
    error_message TEXT,
    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME NULL,

    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_report_user (report_id, user_id),
    INDEX idx_type_date (access_type, accessed_at),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Report access audit trail';

-- ====================================
-- Sample Data
-- ====================================

-- Sample users
INSERT IGNORE INTO users (id, email, name, role) VALUES
(1, 'admin@nilbx.com', 'Admin User', 'admin'),
(2, 'analyst@nilbx.com', 'Business Analyst', 'admin'),
(3, 'sponsor@example.com', 'Nike Representative', 'sponsor');

-- Sample report templates
INSERT INTO report_templates (template_name, template_type, description, sections, export_formats, is_active)
VALUES
    ('Monthly Revenue Report', 'financial', 'Comprehensive monthly revenue analysis',
     '["executive_summary","revenue_breakdown","payment_trends","forecasting"]',
     '["pdf","csv","xlsx","json"]', TRUE),
    ('NIL Deals Report', 'deals', 'Active and completed NIL deals summary',
     '["deal_overview","athlete_breakdown","company_spending","performance_metrics"]',
     '["pdf","xlsx","csv"]', TRUE),
    ('User Analytics Report', 'analytics', 'User engagement and platform usage metrics',
     '["user_growth","engagement_metrics","retention_analysis","demographics"]',
     '["html","pdf","json"]', TRUE),
    ('Payment Compliance Report', 'compliance', 'Payment processing and compliance tracking',
     '["transaction_summary","compliance_status","audit_trail","risk_metrics"]',
     '["pdf","xlsx"]', TRUE),
    ('Athlete Performance Report', 'performance', 'Athlete deal performance and earnings',
     '["earnings_summary","deal_completion","tier_progression","social_metrics"]',
     '["pdf","xlsx","csv"]', TRUE);

-- ====================================
-- Database Verification
-- ====================================
SHOW TABLES;
SELECT 'Reporting Service Database Created - ENHANCED Schema Compatible' as status;
