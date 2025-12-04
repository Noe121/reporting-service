# Reporting Service

A centralized FastAPI-based microservice for report generation, management, and analytics in the NILbx platform. This service handles custom report creation, template management, report scheduling, access logging, and export functionality.

## 🚀 Features

- **Report Generation**: Create custom reports with flexible date ranges and filters
- **Template Management**: Pre-configured report templates for common use cases
- **Report Scheduling**: Automated recurring report generation
- **Access Logging**: Track who views and downloads reports for compliance
- **Export Functionality**: Multi-format report exports (PDF, Excel, CSV)
- **Metrics Tracking**: Performance metrics and analytics for reports
- **Centralized Mode**: Integrates with main NILbx database for unified data access

## 🏗️ Architecture

### Service Overview
- **Framework**: FastAPI with async support
- **Database**: MySQL 8.0 (centralized `nilbx_db`)
- **Port**: 8014 (external), 8014 (container)
- **ORM**: SQLAlchemy with Pydantic models
- **Containerized**: Docker with Python 3.11-slim base

### Operational Modes
The service supports two operational modes:

1. **Centralized Mode** (Default):
   - Uses shared `nilbx_db` database
   - Direct access to platform data
   - Optimal for integrated deployments

2. **Standalone Mode**:
   - Uses separate `reporting_db` database
   - Independent data management
   - Ideal for isolated reporting infrastructure

### Data Flow
1. **Request**: User/system requests report generation
2. **Template**: Load predefined template or custom configuration
3. **Query**: Fetch data based on filters and date ranges
4. **Generate**: Process data into report format
5. **Store**: Save report metadata and results
6. **Export**: Provide download links in multiple formats
7. **Log**: Record access for audit trail

## 📡 API Endpoints

### Health & Status

#### `GET /health`
Health check endpoint with database connectivity status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "mode": "centralized",
  "environment": "dev",
  "database_info": {
    "host": "nilbx-mysql",
    "port": 3306,
    "database": "nilbx_db"
  }
}
```

### Report Endpoints

#### `POST /reports`
Create a new report.

**Query Parameters:**
- `user_id` (int, required): User creating the report
- `template_id` (int, required): Report template to use
- `report_name` (str, required): Name for the report
- `report_type` (str, required): Type of report (financial, operational, user_analytics, compliance)
- `date_range_start` (datetime, required): Start of date range
- `date_range_end` (datetime, required): End of date range

**Request Body:**
```json
{
  "filters": {
    "status": "active",
    "category": "deals"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "report_name": "Q4 2025 Revenue Report",
  "status": "generated",
  "file_url": "/exports/123/download",
  "created_at": "2025-11-07T20:00:00"
}
```

#### `GET /reports/user/{user_id}`
Get all reports for a specific user.

**Path Parameters:**
- `user_id` (int): User ID

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 100)

**Response:**
```json
{
  "reports": [
    {
      "id": 123,
      "report_name": "Q4 2025 Revenue Report",
      "report_type": "financial",
      "status": "generated",
      "generated_at": "2025-11-07T20:00:00"
    }
  ],
  "total": 15,
  "limit": 100,
  "offset": 0
}
```

#### `GET /reports/{report_id}`
Get details of a specific report.

**Path Parameters:**
- `report_id` (int): Report ID

**Response:**
```json
{
  "id": 123,
  "user_id": 456,
  "template_id": 5,
  "report_name": "Q4 2025 Revenue Report",
  "report_type": "financial",
  "status": "generated",
  "date_range_start": "2025-10-01T00:00:00",
  "date_range_end": "2025-12-31T23:59:59",
  "filters": {
    "status": "active"
  },
  "generated_at": "2025-11-07T20:00:00",
  "file_url": "/exports/123/download"
}
```

#### `PATCH /reports/{report_id}/status`
Update report status.

**Path Parameters:**
- `report_id` (int): Report ID

**Query Parameters:**
- `status` (str): New status (pending, generating, generated, failed)

**Response:**
```json
{
  "id": 123,
  "status": "generated",
  "updated_at": "2025-11-07T20:05:00"
}
```

### Access Log Endpoints

#### `GET /access-logs/user/{user_id}`
Get access logs for a user's reports.

**Path Parameters:**
- `user_id` (int): User ID

**Response:**
```json
{
  "access_logs": [
    {
      "id": 1,
      "report_id": 123,
      "user_id": 456,
      "access_type": "view",
      "accessed_at": "2025-11-07T21:00:00",
      "ip_address": "192.168.1.100"
    }
  ],
  "total": 25
}
```

#### `GET /access-logs/report/{report_id}`
Get all access logs for a specific report.

**Path Parameters:**
- `report_id` (int): Report ID

**Response:**
```json
{
  "access_logs": [
    {
      "id": 1,
      "user_id": 456,
      "access_type": "download",
      "accessed_at": "2025-11-07T21:00:00"
    },
    {
      "id": 2,
      "user_id": 789,
      "access_type": "view",
      "accessed_at": "2025-11-07T21:05:00"
    }
  ],
  "total": 2
}
```

#### `GET /access-logs/report/{report_id}/stats`
Get access statistics for a report.

**Path Parameters:**
- `report_id` (int): Report ID

**Response:**
```json
{
  "report_id": 123,
  "total_views": 15,
  "total_downloads": 5,
  "unique_users": 8,
  "last_accessed": "2025-11-07T21:05:00"
}
```

#### `POST /access-logs`
Log a report access event.

**Query Parameters:**
- `report_id` (int, required): Report ID
- `user_id` (int, required): User accessing the report
- `access_type` (str, required): Type of access (view, download, share)

**Response (201 Created):**
```json
{
  "id": 26,
  "report_id": 123,
  "user_id": 456,
  "access_type": "view",
  "accessed_at": "2025-11-07T21:10:00"
}
```

### Export Endpoints

#### `GET /exports`
List all report exports.

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 100)

**Response:**
```json
{
  "exports": [
    {
      "id": 1,
      "report_id": 123,
      "format": "pdf",
      "file_path": "/exports/123.pdf",
      "file_size_bytes": 524288,
      "created_at": "2025-11-07T20:00:00"
    }
  ],
  "total": 50
}
```

#### `GET /exports/report/{report_id}`
Get all exports for a specific report.

**Path Parameters:**
- `report_id` (int): Report ID

**Response:**
```json
{
  "exports": [
    {
      "id": 1,
      "format": "pdf",
      "file_size_bytes": 524288,
      "created_at": "2025-11-07T20:00:00"
    },
    {
      "id": 2,
      "format": "xlsx",
      "file_size_bytes": 1048576,
      "created_at": "2025-11-07T20:01:00"
    }
  ]
}
```

#### `POST /exports`
Create a new export for a report.

**Query Parameters:**
- `report_id` (int, required): Report to export
- `format` (str, required): Export format (pdf, xlsx, csv, json)

**Response (201 Created):**
```json
{
  "id": 3,
  "report_id": 123,
  "format": "csv",
  "file_path": "/exports/123.csv",
  "download_url": "/exports/3/download",
  "created_at": "2025-11-07T21:15:00"
}
```

#### `GET /exports/{export_id}/download`
Download an exported report file.

**Path Parameters:**
- `export_id` (int): Export ID

**Response:**
Binary file download with appropriate Content-Type header.

### Metrics Endpoints

#### `POST /metrics`
Record a report performance metric.

**Query Parameters:**
- `report_id` (int, required): Report ID
- `metric_name` (str, required): Metric name (generation_time, file_size, row_count)
- `metric_value` (float, required): Metric value
- `metric_unit` (str, required): Unit of measurement (seconds, bytes, count)
- `metric_category` (str, optional): Category (default: performance)

**Response (201 Created):**
```json
{
  "id": 1,
  "report_id": 123,
  "metric_name": "generation_time",
  "metric_value": 2.45,
  "metric_unit": "seconds",
  "recorded_at": "2025-11-07T20:00:00"
}
```

#### `GET /metrics/report/{report_id}`
Get all metrics for a specific report.

**Path Parameters:**
- `report_id` (int): Report ID

**Response:**
```json
{
  "metrics": [
    {
      "metric_name": "generation_time",
      "metric_value": 2.45,
      "metric_unit": "seconds",
      "recorded_at": "2025-11-07T20:00:00"
    },
    {
      "metric_name": "file_size",
      "metric_value": 524288,
      "metric_unit": "bytes",
      "recorded_at": "2025-11-07T20:00:00"
    }
  ]
}
```

#### `GET /metrics/average/{metric_name}`
Get average value for a specific metric across all reports.

**Path Parameters:**
- `metric_name` (str): Metric name

**Response:**
```json
{
  "metric_name": "generation_time",
  "average_value": 3.67,
  "metric_unit": "seconds",
  "sample_count": 150
}
```

#### `GET /metrics/category/{category}`
Get metrics filtered by category.

**Path Parameters:**
- `category` (str): Metric category

**Response:**
```json
{
  "category": "performance",
  "metrics": [
    {
      "metric_name": "generation_time",
      "avg_value": 3.67,
      "min_value": 0.89,
      "max_value": 12.34
    }
  ]
}
```

### Schedule Endpoints

#### `POST /schedules`
Create a report schedule for recurring reports.

**Query Parameters:**
- `user_id` (int, required): User creating the schedule
- `template_id` (int, required): Report template
- `frequency` (str, required): Schedule frequency (daily, weekly, monthly)
- `next_run` (datetime, required): Next scheduled execution time

**Request Body:**
```json
{
  "filters": {
    "status": "active"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 456,
  "template_id": 5,
  "frequency": "weekly",
  "is_active": true,
  "next_run": "2025-11-14T00:00:00",
  "created_at": "2025-11-07T21:20:00"
}
```

#### `GET /schedules/user/{user_id}`
Get all report schedules for a user.

**Path Parameters:**
- `user_id` (int): User ID

**Response:**
```json
{
  "schedules": [
    {
      "id": 1,
      "template_id": 5,
      "frequency": "weekly",
      "is_active": true,
      "last_run": "2025-11-07T00:00:00",
      "next_run": "2025-11-14T00:00:00"
    }
  ],
  "total": 3
}
```

#### `GET /schedules/due`
Get all schedules that are due for execution.

**Response:**
```json
{
  "schedules": [
    {
      "id": 1,
      "user_id": 456,
      "template_id": 5,
      "next_run": "2025-11-07T22:00:00"
    }
  ],
  "count": 5
}
```

#### `PATCH /schedules/{schedule_id}`
Update a report schedule.

**Path Parameters:**
- `schedule_id` (int): Schedule ID

**Request Body:**
```json
{
  "is_active": false
}
```

**Response:**
```json
{
  "id": 1,
  "is_active": false,
  "updated_at": "2025-11-07T21:25:00"
}
```

## 🗄️ Database Schema

### Tables (Centralized Mode - nilbx_db)

The service uses shared tables in the main platform database:

#### `reports`
```sql
CREATE TABLE reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    template_id INT,
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    status ENUM('pending', 'generating', 'generated', 'failed') DEFAULT 'pending',
    date_range_start DATETIME NOT NULL,
    date_range_end DATETIME NOT NULL,
    filters JSON,
    file_url VARCHAR(500),
    generated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_type (report_type),
    INDEX idx_generated (generated_at)
);
```

#### `report_templates`
```sql
CREATE TABLE report_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(100) NOT NULL,
    description TEXT,
    default_filters JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_type (template_type)
);
```

#### `report_access_logs`
```sql
CREATE TABLE report_access_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    user_id INT NOT NULL,
    access_type ENUM('view', 'download', 'share') NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_report (report_id),
    INDEX idx_user (user_id),
    INDEX idx_accessed (accessed_at)
);
```

#### `report_exports`
```sql
CREATE TABLE report_exports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    format VARCHAR(20) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,

    INDEX idx_report (report_id),
    INDEX idx_format (format)
);
```

#### `report_metrics`
```sql
CREATE TABLE report_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 2) NOT NULL,
    metric_unit VARCHAR(50),
    metric_category VARCHAR(50) DEFAULT 'performance',
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,

    INDEX idx_report (report_id),
    INDEX idx_metric (metric_name),
    INDEX idx_category (metric_category)
);
```

#### `report_schedules`
```sql
CREATE TABLE report_schedules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    template_id INT NOT NULL,
    frequency ENUM('daily', 'weekly', 'monthly') NOT NULL,
    filters JSON,
    is_active BOOLEAN DEFAULT TRUE,
    last_run DATETIME,
    next_run DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE CASCADE,

    INDEX idx_user (user_id),
    INDEX idx_active (is_active),
    INDEX idx_next_run (next_run)
);
```

## 🚀 Setup and Installation

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Docker & Docker Compose (for containerized setup)

### Local Development Setup

1. **Navigate to directory:**
   ```bash
   cd reporting-service
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   export DB_HOST=localhost
   export DB_PORT=3306
   export DB_NAME=nilbx_db
   export DB_USER=root
   export DB_PASSWORD=rootpassword
   export MODE=centralized  # or 'standalone'
   ```

5. **Run the service:**
   ```bash
   cd src
   uvicorn main:app --reload --host 0.0.0.0 --port 8014
   ```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the service
# API: http://localhost:8014
# Docs: http://localhost:8014/docs
```

### Access the Service

- **API**: http://localhost:8014
- **API Documentation**: http://localhost:8014/docs
- **OpenAPI Spec**: http://localhost:8014/openapi.json

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_HOST` | MySQL host | `localhost` | Yes |
| `DB_PORT` | MySQL port | `3306` | Yes |
| `DB_NAME` | Database name | `nilbx_db` | Yes |
| `DB_USER` | Database user | `root` | Yes |
| `DB_PASSWORD` | Database password | `rootpassword` | Yes |
| `MODE` | Operation mode | `centralized` | No |

### Operational Modes

**Centralized Mode** (Default):
```bash
export MODE=centralized
export DB_NAME=nilbx_db
```

**Standalone Mode**:
```bash
export MODE=standalone
export DB_NAME=reporting_db
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_reporting_service.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite includes:
- ✅ Health check and connectivity
- ✅ Report creation and retrieval
- ✅ Access logging functionality
- ✅ Export generation (PDF, Excel, CSV)
- ✅ Metrics recording and aggregation
- ✅ Schedule management
- ✅ Database integration tests
- ✅ Error handling scenarios

## 🚢 Deployment

### Container Deployment

```bash
# Build the image
docker build -t reporting-service .

# Run the container
docker run -d \
  --name reporting-service \
  -e DB_HOST=nilbx-mysql \
  -e DB_NAME=nilbx_db \
  -e DB_USER=root \
  -e DB_PASSWORD=rootpassword \
  -p 8014:8014 \
  reporting-service
```

### Production Deployment

For production:

1. **Secure database credentials** using secrets management
2. **Enable HTTPS** with reverse proxy
3. **Configure S3** for report file storage
4. **Set up monitoring** (CloudWatch, DataDog)
5. **Enable rate limiting** at API gateway
6. **Configure backup** for report data

## 🔧 Development

### Code Structure

```
reporting-service/
├── src/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   └── config.py            # Configuration management
├── tests/
│   └── test_reporting_service.py
├── Dockerfile               # Container definition
├── docker-compose.yml       # Local development setup
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Key Components

- **main.py**: FastAPI application with all API endpoints
- **models.py**: SQLAlchemy models for database tables
- **config.py**: Environment configuration and database setup

## 🤝 Integration

### Service Dependencies

- **MySQL Database**: Shared `nilbx_db` or dedicated `reporting_db`
- **Admin Dashboard**: Report schedule management integration
- **Storage Service**: S3 or local storage for report files
- **Authentication**: JWT token validation

### Frontend Integration

The service integrates with multiple frontend platforms:

- **iOS**: ReportTemplatesView.swift - SwiftUI reporting interface
- **Android**: ReportTemplatesScreen.kt - Jetpack Compose reporting interface
- **Web**: React reporting dashboard components

## 📊 Monitoring

### Health Checks

- **Endpoint**: `GET /health`
- **Metrics**: Database connectivity, operational mode
- **Dependencies**: MySQL connection status

### Logging

- **Format**: Structured JSON logging
- **Levels**: INFO, WARNING, ERROR, CRITICAL
- **Access Logs**: All report accesses tracked

### Metrics

Key metrics to monitor:
- Report generation time
- Export file sizes
- Access frequency
- Database query performance
- Error rates by report type

## 🔒 Security

### Authentication

- User-ID based access control
- JWT token validation (when integrated with auth service)

### Data Protection

- **Access Logs**: Comprehensive audit trail
- **SQL Injection**: Protected via SQLAlchemy parameterized queries
- **CCPA Compliance**: Full access logging for data requests

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```
Error: Can't connect to MySQL server
```
**Solutions:**
- Check MySQL service: `docker ps | grep mysql`
- Verify credentials in environment variables
- Ensure database exists: `nilbx_db`

#### 2. Report Generation Failed
```
Error: Report generation failed
```
**Solutions:**
- Check template_id is valid
- Verify date range parameters
- Review database query permissions

## 📄 License

This service is part of the NILbx platform. See main project license for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

**Service Status**: ✅ Production Ready
**Current Version**: 1.0.0
**Last Updated**: November 7, 2025
**Maintained by**: NILbx Platform Team
