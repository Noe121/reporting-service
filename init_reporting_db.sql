-- Reporting Service Database Schema

-- Report Templates Table
CREATE TABLE IF NOT EXISTS report_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    template_type VARCHAR(50) NOT NULL,
    description TEXT,
    sections LONGTEXT,
    export_formats LONGTEXT,
    is_default TINYINT DEFAULT 0,
    is_active TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0,
    deleted_at TIMESTAMP NULL,
    INDEX idx_report_templates_type_active (template_type, is_active),
    INDEX idx_report_templates_name (template_name)
);

-- Reports Table
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
    generated_at TIMESTAMP NULL,
    generation_time_seconds DECIMAL(10, 2),
    file_path VARCHAR(500),
    file_size INT,
    error_message TEXT,
    filters LONGTEXT,
    generated_by VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (template_id) REFERENCES report_templates(id),
    INDEX idx_reports_user_status (user_id, status),
    INDEX idx_reports_type_created (report_type, created_at),
    INDEX idx_reports_generated_status (generated_at, status)
);

-- Report Schedules Table
CREATE TABLE IF NOT EXISTS report_schedules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    template_id INT NOT NULL,
    schedule_name VARCHAR(100) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    time_of_day VARCHAR(10) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    recipients LONGTEXT,
    delivery_method VARCHAR(50) DEFAULT 'email',
    is_enabled TINYINT DEFAULT 1,
    next_run_at DATETIME,
    last_run_at TIMESTAMP NULL,
    run_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (template_id) REFERENCES report_templates(id),
    INDEX idx_report_schedules_user_enabled (user_id, is_enabled),
    INDEX idx_report_schedules_next_run (next_run_at)
);

-- Report Exports Table
CREATE TABLE IF NOT EXISTS report_exports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    export_format VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT,
    file_hash VARCHAR(128),
    export_status VARCHAR(50) DEFAULT 'pending',
    exported_at TIMESTAMP NULL,
    download_count INT DEFAULT 0,
    last_downloaded_at TIMESTAMP NULL,
    error_message TEXT,
    compression VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (report_id) REFERENCES reports(id),
    INDEX idx_report_exports_report_format (report_id, export_format),
    INDEX idx_report_exports_status (export_status)
);

-- Report Metrics Table
CREATE TABLE IF NOT EXISTS report_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4) NOT NULL,
    metric_unit VARCHAR(50) NOT NULL,
    metric_category VARCHAR(50) DEFAULT 'performance',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (report_id) REFERENCES reports(id),
    INDEX idx_report_metrics_report_name (report_id, metric_name),
    INDEX idx_report_metrics_category (metric_category)
);

-- Report Access Logs Table
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
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (report_id) REFERENCES reports(id),
    INDEX idx_report_access_logs_report_user (report_id, user_id),
    INDEX idx_report_access_logs_type_date (access_type, accessed_at)
);

-- Sample Data
INSERT INTO report_templates (template_name, template_type, description, sections, export_formats, is_active)
VALUES 
    ('Monthly Sales Report', 'sales', 'Comprehensive monthly sales analysis', 
     '["executive_summary","regional_breakdown","product_performance","trends","recommendations"]',
     '["pdf","csv","xlsx","json"]', 1),
    ('Analytics Dashboard', 'analytics', 'User engagement and usage metrics',
     '["overview","user_metrics","engagement_trends","behavior_analysis"]',
     '["html","json","pdf"]', 1),
    ('Financial Statement', 'financial', 'Monthly financial summary',
     '["income_statement","balance_sheet","cash_flow","ratios"]',
     '["pdf","xlsx"]', 1);
