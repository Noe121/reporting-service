"""
Reporting Service Models

Comprehensive data models for report generation, scheduling, export management,
and performance tracking. Features soft delete pattern and strategic database indexing.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    VARCHAR,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ReportTemplate(Base):
    """
    Report Templates
    Reusable templates for standard reports with customizable sections
    """

    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String(100), nullable=False, unique=True)
    template_type = Column(String(50), nullable=False)  # sales, analytics, financial, custom
    description = Column(Text)
    sections = Column(Text)  # JSON array of sections: summary, charts, tables, metrics
    export_formats = Column(Text)  # JSON array: pdf, csv, xlsx, json, html
    is_default = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_report_templates_type_active", "template_type", "is_active"),
        Index("idx_report_templates_name", "template_name"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "template_name": self.template_name,
            "template_type": self.template_type,
            "description": self.description,
            "is_default": bool(self.is_default),
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class Report(Base):
    """
    Reports
    Core report entity tracking status, generation time, and output formats
    """

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)
    date_range_start = Column(DateTime, nullable=False)
    date_range_end = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)  # draft, generating, ready, failed, archived
    progress_percent = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    rows_generated = Column(Integer, default=0)
    generated_at = Column(DateTime)
    generated_by = Column(String(50))  # system, manual, scheduled
    file_path = Column(String(500))
    file_size = Column(Integer)
    export_formats = Column(Text)  # JSON array of formats available
    filters = Column(Text)  # JSON filters applied
    error_message = Column(Text)
    generation_time_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_reports_user_status", "user_id", "status"),
        Index("idx_reports_type_created", "report_type", "created_at"),
        Index("idx_reports_generated_status", "status", "generated_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "report_name": self.report_name,
            "report_type": self.report_type,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start is not None else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end is not None else None,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "total_records": self.total_records,
            "generated_at": self.generated_at.isoformat() if self.generated_at is not None else None,
            "file_size": self.file_size,
            "generation_time_seconds": self.generation_time_seconds,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class ReportSchedule(Base):
    """
    Report Schedules
    Recurring report generation with frequency and distribution settings
    """

    __tablename__ = "report_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    schedule_name = Column(String(255), nullable=False)
    frequency = Column(String(50), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    day_of_week = Column(Integer)  # 0-6 for weekly (0=Monday)
    day_of_month = Column(Integer)  # 1-31 for monthly
    time_of_day = Column(String(5))  # HH:MM format
    timezone = Column(String(50), default="UTC")
    is_enabled = Column(Integer, default=1)
    next_run_at = Column(DateTime)
    last_run_at = Column(DateTime)
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    recipients = Column(Text)  # JSON array of email addresses
    delivery_method = Column(String(50))  # email, download, webhook
    webhook_url = Column(String(500))
    include_file = Column(Integer, default=1)  # Whether to include report file
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_report_schedules_user_enabled", "user_id", "is_enabled"),
        Index("idx_report_schedules_next_run", "next_run_at", "is_enabled"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "schedule_name": self.schedule_name,
            "frequency": self.frequency,
            "is_enabled": bool(self.is_enabled),
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at is not None else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at is not None else None,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class ReportExport(Base):
    """
    Report Exports
    Track exported report files and their formats
    """

    __tablename__ = "report_exports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    export_format = Column(String(20), nullable=False)  # pdf, csv, xlsx, json, html
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_hash = Column(String(100))  # SHA-256 for integrity
    export_status = Column(String(50), nullable=False)  # pending, processing, completed, failed
    exported_at = Column(DateTime)
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime)
    compression_type = Column(String(20))  # none, gzip, zip
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_report_exports_report_format", "report_id", "export_format"),
        Index("idx_report_exports_status", "export_status", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "export_format": self.export_format,
            "file_size": self.file_size,
            "export_status": self.export_status,
            "exported_at": self.exported_at.isoformat() if self.exported_at is not None else None,
            "download_count": self.download_count,
            "last_downloaded_at": self.last_downloaded_at.isoformat() if self.last_downloaded_at is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class ReportMetric(Base):
    """
    Report Metrics
    Performance and usage metrics for reports
    """

    __tablename__ = "report_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)  # generation_time, page_count, data_points, etc.
    metric_value = Column(Numeric(12, 2), nullable=False)
    metric_unit = Column(String(50))  # seconds, pages, items, bytes, etc.
    metric_category = Column(String(50))  # performance, usage, quality
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_report_metrics_report_name", "report_id", "metric_name"),
        Index("idx_report_metrics_category", "metric_category", "recorded_at"),
    )

    def to_dict(self):
        metric_value = float(self.metric_value) if self.metric_value is not None else 0.0  # type: ignore[reportArgumentType]
        return {
            "id": self.id,
            "report_id": self.report_id,
            "metric_name": self.metric_name,
            "metric_value": metric_value,
            "metric_unit": self.metric_unit,
            "metric_category": self.metric_category,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at is not None else None,
        }


class ReportAccess(Base):
    """
    Report Access Log
    Track who accessed reports and when
    """

    __tablename__ = "report_access_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    access_type = Column(String(50), nullable=False)  # view, download, share, print
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    access_status = Column(String(50))  # success, denied, error
    error_message = Column(Text)
    access_duration_seconds = Column(Integer)
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_report_access_report_user", "report_id", "user_id"),
        Index("idx_report_access_type_date", "access_type", "accessed_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "user_id": self.user_id,
            "access_type": self.access_type,
            "access_status": self.access_status,
            "access_duration_seconds": self.access_duration_seconds,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at is not None else None,
        }
