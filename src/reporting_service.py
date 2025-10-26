"""
Reporting Service - Business Logic Layer

Comprehensive report management including template handling, scheduling,
export coordination, and performance tracking.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from .models import (
    ReportTemplate,
    Report,
    ReportSchedule,
    ReportExport,
    ReportMetric,
    ReportAccess,
    Base,
)

logger = logging.getLogger(__name__)


class ReportTemplateService:
    """Manage report templates"""

    @staticmethod
    def create_template(
        db: Session,
        template_name: str,
        template_type: str,
        description: Optional[str] = None,
        sections: Optional[List[str]] = None,
        export_formats: Optional[List[str]] = None,
        is_default: bool = False,
    ) -> ReportTemplate:
        """Create a new report template"""
        template = ReportTemplate(
            template_name=template_name,
            template_type=template_type,
            description=description,
            sections=json.dumps(sections) if sections else None,
            export_formats=json.dumps(export_formats or ["pdf", "csv", "json"]),
            is_default=1 if is_default else 0,
            is_active=1,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[ReportTemplate]:
        """Get template by ID"""
        return (
            db.query(ReportTemplate)
            .filter(ReportTemplate.id == template_id, ReportTemplate.is_deleted == 0)
            .first()
        )

    @staticmethod
    def get_templates_by_type(
        db: Session, template_type: str, limit: int = 100, offset: int = 0
    ) -> Tuple[List[ReportTemplate], int]:
        """Get templates by type"""
        query = db.query(ReportTemplate).filter(
            ReportTemplate.template_type == template_type, ReportTemplate.is_deleted == 0
        )
        total = query.count()
        templates = query.order_by(ReportTemplate.created_at.desc()).offset(offset).limit(limit).all()
        return templates, total

    @staticmethod
    def list_active_templates(db: Session, limit: int = 100, offset: int = 0) -> Tuple[List[ReportTemplate], int]:
        """List all active templates"""
        query = db.query(ReportTemplate).filter(
            ReportTemplate.is_deleted == 0, ReportTemplate.is_active == 1
        )
        total = query.count()
        templates = query.order_by(ReportTemplate.created_at.desc()).offset(offset).limit(limit).all()
        return templates, total


class ReportGenerationService:
    """Manage report generation"""

    @staticmethod
    def create_report(
        db: Session,
        user_id: int,
        template_id: int,
        report_name: str,
        report_type: str,
        date_range_start: datetime,
        date_range_end: datetime,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Report:
        """Create a new report"""
        report = Report(
            user_id=user_id,
            template_id=template_id,
            report_name=report_name,
            report_type=report_type,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            status="draft",
            progress_percent=0,
            filters=json.dumps(filters) if filters else None,
            generated_by="manual",
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def update_report_status(
        db: Session,
        report_id: int,
        status: str,
        progress_percent: int = 0,
        rows_generated: int = 0,
    ) -> Optional[Report]:
        """Update report generation status"""
        report = db.query(Report).filter(Report.id == report_id, Report.is_deleted == 0).first()
        if report:
            report.status = status  # type: ignore[reportAttributeAccessIssue]
            report.progress_percent = progress_percent  # type: ignore[reportAttributeAccessIssue]
            report.rows_generated = rows_generated  # type: ignore[reportAttributeAccessIssue]
            db.commit()
            db.refresh(report)
        return report

    @staticmethod
    def mark_report_completed(
        db: Session,
        report_id: int,
        total_records: int,
        generation_time: float,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> Optional[Report]:
        """Mark report as completed"""
        report = db.query(Report).filter(Report.id == report_id, Report.is_deleted == 0).first()
        if report:
            report.status = "ready"  # type: ignore[reportAttributeAccessIssue]
            report.total_records = total_records  # type: ignore[reportAttributeAccessIssue]
            report.rows_generated = total_records  # type: ignore[reportAttributeAccessIssue]
            report.progress_percent = 100  # type: ignore[reportAttributeAccessIssue]
            report.generated_at = datetime.utcnow()  # type: ignore[reportAttributeAccessIssue]
            report.generation_time_seconds = generation_time  # type: ignore[reportAttributeAccessIssue]
            if file_path:
                report.file_path = file_path  # type: ignore[reportAttributeAccessIssue]
            if file_size:
                report.file_size = file_size  # type: ignore[reportAttributeAccessIssue]
            db.commit()
            db.refresh(report)
        return report

    @staticmethod
    def mark_report_failed(db: Session, report_id: int, error_message: str) -> Optional[Report]:
        """Mark report as failed"""
        report = db.query(Report).filter(Report.id == report_id, Report.is_deleted == 0).first()
        if report:
            report.status = "failed"  # type: ignore[reportAttributeAccessIssue]
            report.error_message = error_message  # type: ignore[reportAttributeAccessIssue]
            db.commit()
            db.refresh(report)
        return report

    @staticmethod
    def get_user_reports(
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Report], int]:
        """Get user reports with optional status filtering"""
        query = db.query(Report).filter(Report.user_id == user_id, Report.is_deleted == 0)
        if status:
            query = query.filter(Report.status == status)
        total = query.count()
        reports = query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()
        return reports, total

    @staticmethod
    def get_report(db: Session, report_id: int, user_id: Optional[int] = None) -> Optional[Report]:
        """Get report by ID"""
        query = db.query(Report).filter(Report.id == report_id, Report.is_deleted == 0)
        if user_id:
            query = query.filter(Report.user_id == user_id)
        return query.first()


class ReportScheduleService:
    """Manage report scheduling"""

    @staticmethod
    def create_schedule(
        db: Session,
        user_id: int,
        template_id: int,
        schedule_name: str,
        frequency: str,
        time_of_day: str,
        timezone: str = "UTC",
        recipients: Optional[List[str]] = None,
        delivery_method: str = "email",
    ) -> ReportSchedule:
        """Create a new report schedule"""
        schedule = ReportSchedule(
            user_id=user_id,
            template_id=template_id,
            schedule_name=schedule_name,
            frequency=frequency,
            time_of_day=time_of_day,
            timezone=timezone,
            recipients=json.dumps(recipients) if recipients else None,
            delivery_method=delivery_method,
            is_enabled=1,
        )
        # Set initial next_run_at
        setattr(schedule, "next_run_at", ReportScheduleService._calculate_next_run(frequency, time_of_day))
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def _calculate_next_run(frequency: str, time_of_day: str) -> datetime:
        """Calculate next run time based on frequency"""
        now = datetime.utcnow()
        hour, minute = map(int, time_of_day.split(":"))
        
        if frequency == "daily":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == "weekly":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=7)
        elif frequency == "monthly":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0, day=1)
            if next_run <= now:
                next_run += timedelta(days=32)
                next_run = next_run.replace(day=1)
        else:
            next_run = now + timedelta(days=1)
        
        return next_run

    @staticmethod
    def get_schedules_due_for_execution(db: Session) -> List[ReportSchedule]:
        """Get schedules that are due for execution"""
        now = datetime.utcnow()
        return (
            db.query(ReportSchedule)
            .filter(
                ReportSchedule.is_enabled == 1,
                ReportSchedule.next_run_at <= now,
                ReportSchedule.is_deleted == 0,
            )
            .all()
        )

    @staticmethod
    def update_schedule_after_execution(
        db: Session, schedule_id: int, success: bool
    ) -> Optional[ReportSchedule]:
        """Update schedule after execution"""
        schedule = (
            db.query(ReportSchedule)
            .filter(ReportSchedule.id == schedule_id, ReportSchedule.is_deleted == 0)
            .first()
        )
        if schedule:
            schedule.last_run_at = datetime.utcnow()  # type: ignore[reportAttributeAccessIssue]
            schedule.run_count += 1  # type: ignore[reportAttributeAccessIssue]
            if success:
                schedule.success_count += 1  # type: ignore[reportAttributeAccessIssue]
            else:
                schedule.failure_count += 1  # type: ignore[reportAttributeAccessIssue]
                setattr(
                    schedule,
                    "next_run_at",
                    ReportScheduleService._calculate_next_run(
                        getattr(schedule, "frequency", "daily"),
                        getattr(schedule, "time_of_day", "00:00")
                    )
                )
            db.commit()
            db.refresh(schedule)
        return schedule

    @staticmethod
    def get_user_schedules(
        db: Session, user_id: int, limit: int = 100, offset: int = 0
    ) -> Tuple[List[ReportSchedule], int]:
        """Get schedules for a user"""
        query = db.query(ReportSchedule).filter(
            ReportSchedule.user_id == user_id, ReportSchedule.is_deleted == 0
        )
        total = query.count()
        schedules = query.order_by(ReportSchedule.created_at.desc()).offset(offset).limit(limit).all()
        return schedules, total


class ReportExportService:
    """Manage report exports"""

    @staticmethod
    def create_export(
        db: Session,
        report_id: int,
        export_format: str,
        file_path: str,
        file_size: Optional[int] = None,
    ) -> ReportExport:
        """Create a new report export"""
        export = ReportExport(
            report_id=report_id,
            export_format=export_format,
            file_path=file_path,
            file_size=file_size,
            export_status="pending",
        )
        db.add(export)
        db.commit()
        db.refresh(export)
        return export

    @staticmethod
    def mark_export_completed(
        db: Session,
        export_id: int,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None,
    ) -> Optional[ReportExport]:
        """Mark export as completed"""
        export = (
            db.query(ReportExport)
            .filter(ReportExport.id == export_id, ReportExport.is_deleted == 0)
            .first()
        )
        if export:
            export.export_status = "completed"  # type: ignore[reportAttributeAccessIssue]
            export.exported_at = datetime.utcnow()  # type: ignore[reportAttributeAccessIssue]
            if file_size:
                export.file_size = file_size  # type: ignore[reportAttributeAccessIssue]
            if file_hash:
                export.file_hash = file_hash  # type: ignore[reportAttributeAccessIssue]
            db.commit()
            db.refresh(export)
        return export

    @staticmethod
    def mark_export_failed(db: Session, export_id: int, error_message: str) -> Optional[ReportExport]:
        """Mark export as failed"""
        export = (
            db.query(ReportExport)
            .filter(ReportExport.id == export_id, ReportExport.is_deleted == 0)
            .first()
        )
        if export:
            export.export_status = "failed"  # type: ignore[reportAttributeAccessIssue]
            export.error_message = error_message  # type: ignore[reportAttributeAccessIssue]
            db.commit()
            db.refresh(export)
        return export

    @staticmethod
    def record_download(db: Session, export_id: int) -> Optional[ReportExport]:
        """Record an export download"""
        export = (
            db.query(ReportExport)
            .filter(ReportExport.id == export_id, ReportExport.is_deleted == 0)
            .first()
        )
        if export:
            export.download_count += 1  # type: ignore[reportAttributeAccessIssue]
            export.last_downloaded_at = datetime.utcnow()  # type: ignore[reportAttributeAccessIssue]
            db.commit()
            db.refresh(export)
        return export

    @staticmethod
    def get_report_exports(
        db: Session, report_id: int, limit: int = 100, offset: int = 0
    ) -> Tuple[List[ReportExport], int]:
        """Get exports for a report"""
        query = db.query(ReportExport).filter(
            ReportExport.report_id == report_id, ReportExport.is_deleted == 0
        )
        total = query.count()
        exports = query.order_by(ReportExport.created_at.desc()).offset(offset).limit(limit).all()
        return exports, total


class ReportMetricsService:
    """Manage report metrics and performance tracking"""

    @staticmethod
    def record_metric(
        db: Session,
        report_id: int,
        metric_name: str,
        metric_value: float,
        metric_unit: str,
        metric_category: str = "performance",
    ) -> ReportMetric:
        """Record a report metric"""
        metric = ReportMetric(
            report_id=report_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            metric_category=metric_category,
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric

    @staticmethod
    def get_report_metrics(
        db: Session, report_id: int, limit: int = 100, offset: int = 0
    ) -> Tuple[List[ReportMetric], int]:
        """Get metrics for a report"""
        query = db.query(ReportMetric).filter(
            ReportMetric.report_id == report_id, ReportMetric.is_deleted == 0
        )
        total = query.count()
        metrics = query.order_by(ReportMetric.recorded_at.desc()).offset(offset).limit(limit).all()
        return metrics, total

    @staticmethod
    def get_metrics_by_category(
        db: Session, category: str, limit: int = 100, offset: int = 0
    ) -> Tuple[List[ReportMetric], int]:
        """Get metrics by category"""
        query = db.query(ReportMetric).filter(
            ReportMetric.metric_category == category, ReportMetric.is_deleted == 0
        )
        total = query.count()
        metrics = query.order_by(ReportMetric.recorded_at.desc()).offset(offset).limit(limit).all()
        return metrics, total

    @staticmethod
    def get_average_metrics(db: Session, metric_name: str, days: int = 30) -> Dict[str, Any]:
        """Get average metrics over time period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        metrics = (
            db.query(ReportMetric)
            .filter(
                ReportMetric.metric_name == metric_name,
                ReportMetric.recorded_at >= cutoff_date,
                ReportMetric.is_deleted == 0,
            )
            .all()
        )
        
        if not metrics:
            return {"average": 0, "count": 0, "min": 0, "max": 0}
        
        values = [float(m.metric_value) for m in metrics]  # type: ignore[reportArgumentType]
        return {
            "average": sum(values) / len(values),
            "count": len(values),
            "min": min(values),
            "max": max(values),
        }


class ReportAccessService:
    """Manage report access logging and auditing"""

    @staticmethod
    def log_access(
        db: Session,
        report_id: int,
        user_id: int,
        access_type: str,
        access_status: str = "success",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> ReportAccess:
        """Log report access"""
        log = ReportAccess(
            report_id=report_id,
            user_id=user_id,
            access_type=access_type,
            access_status=access_status,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
            access_duration_seconds=duration_seconds,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_report_access_logs(
        db: Session, report_id: int, limit: int = 100, offset: int = 0
    ) -> Tuple[List[ReportAccess], int]:
        """Get access logs for a report"""
        query = db.query(ReportAccess).filter(
            ReportAccess.report_id == report_id, ReportAccess.is_deleted == 0
        )
        total = query.count()
        logs = query.order_by(ReportAccess.accessed_at.desc()).offset(offset).limit(limit).all()
        return logs, total

    @staticmethod
    def get_user_access_logs(
        db: Session, user_id: int, limit: int = 100, offset: int = 0
    ) -> Tuple[List[ReportAccess], int]:
        """Get access logs for a user"""
        query = db.query(ReportAccess).filter(
            ReportAccess.user_id == user_id, ReportAccess.is_deleted == 0
        )
        total = query.count()
        logs = query.order_by(ReportAccess.accessed_at.desc()).offset(offset).limit(limit).all()
        return logs, total

    @staticmethod
    def get_access_statistics(db: Session, report_id: int) -> Dict[str, Any]:
        """Get access statistics for a report"""
        logs = (
            db.query(ReportAccess)
            .filter(ReportAccess.report_id == report_id, ReportAccess.is_deleted == 0)
            .all()
        )
        
        if not logs:
            return {
                "total_accesses": 0,
                "successful": 0,
                "failed": 0,
                "by_type": {},
                "unique_users": 0,
            }
        
        by_type = {}
        for log in logs:
            if log.access_type not in by_type:
                by_type[log.access_type] = 0
            by_type[log.access_type] += 1
        
        unique_users = len(set(log.user_id for log in logs))
        successful = len([l for l in logs if getattr(l, "access_status", None) == "success"])
        return {
            "total_accesses": len(logs),
            "successful": successful,
            "failed": len(logs) - successful,
            "by_type": by_type,
            "unique_users": unique_users,
        }
