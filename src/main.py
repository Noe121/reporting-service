"""
Reporting Service - FastAPI Application

REST API endpoints for report generation, scheduling, export management,
and performance tracking.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Generator

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Create FastAPI app first
app = FastAPI(
    title="Reporting Service",
    description="Report generation, scheduling, export, and analytics",
    version="1.0.0",
)

# Import models after app creation
from models import Base

# Initialize database
DATABASE_URL = "sqlite:///./reporting_service.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from reporting_service import (
    ReportTemplateService,
    ReportGenerationService,
    ReportScheduleService,
    ReportExportService,
    ReportMetricsService,
    ReportAccessService,
)


# ============================================================================
# REPORT TEMPLATE ENDPOINTS
# ============================================================================


@app.post("/templates", status_code=201)
async def create_report_template(
    template_name: str,
    template_type: str,
    description: Optional[str] = None,
    sections: Optional[List[str]] = None,
    export_formats: Optional[List[str]] = None,
    is_default: bool = False,
    db: Session = Depends(get_db),
):
    """Create a new report template"""
    try:
        template = ReportTemplateService.create_template(
            db=db,
            template_name=template_name,
            template_type=template_type,
            description=description,
            sections=sections,
            export_formats=export_formats,
            is_default=is_default,
        )
        return {
            "id": template.id,
            "template_name": template.template_name,
            "template_type": template.template_type,
            "created_at": template.created_at,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/templates/{template_id}")
async def get_report_template(template_id: int, db: Session = Depends(get_db)):
    """Get template by ID"""
    template = ReportTemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@app.get("/templates/type/{template_type}")
async def get_templates_by_type(
    template_type: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get templates by type"""
    templates, total = ReportTemplateService.get_templates_by_type(
        db, template_type, limit, offset
    )
    return {
        "templates": [t.to_dict() for t in templates],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/templates")
async def list_templates(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all active templates"""
    templates, total = ReportTemplateService.list_active_templates(db, limit, offset)
    return {
        "templates": [t.to_dict() for t in templates],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ============================================================================
# REPORT GENERATION ENDPOINTS
# ============================================================================


@app.post("/reports", status_code=201)
async def create_report(
    user_id: int,
    template_id: int,
    report_name: str,
    report_type: str,
    date_range_start: datetime,
    date_range_end: datetime,
    filters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
):
    """Create a new report"""
    try:
        # Validate template exists
        template = ReportTemplateService.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        report = ReportGenerationService.create_report(
            db=db,
            user_id=user_id,
            template_id=template_id,
            report_name=report_name,
            report_type=report_type,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            filters=filters,
        )
        return {
            "id": report.id,
            "report_name": report.report_name,
            "status": report.status,
            "created_at": report.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Get report by ID"""
    report = ReportGenerationService.get_report(db, report_id, user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report.to_dict()


@app.get("/reports/user/{user_id}")
async def get_user_reports(
    user_id: int,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get user reports"""
    reports, total = ReportGenerationService.get_user_reports(
        db, user_id, status, limit, offset
    )
    return {
        "reports": [r.to_dict() for r in reports],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.patch("/reports/{report_id}/status")
async def update_report_status(
    report_id: int,
    status: str,
    progress_percent: int = 0,
    db: Session = Depends(get_db),
):
    """Update report status"""
    report = ReportGenerationService.update_report_status(
        db, report_id, status, progress_percent
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": report.status, "progress": report.progress_percent}


# ============================================================================
# REPORT SCHEDULING ENDPOINTS
# ============================================================================


@app.post("/schedules", status_code=201)
async def create_schedule(
    user_id: int,
    template_id: int,
    schedule_name: str,
    frequency: str,
    time_of_day: str,
    timezone: str = "UTC",
    recipients: Optional[List[str]] = None,
    delivery_method: str = "email",
    db: Session = Depends(get_db),
):
    """Create a report schedule"""
    try:
        # Validate template exists
        template = ReportTemplateService.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        schedule = ReportScheduleService.create_schedule(
            db=db,
            user_id=user_id,
            template_id=template_id,
            schedule_name=schedule_name,
            frequency=frequency,
            time_of_day=time_of_day,
            timezone=timezone,
            recipients=recipients,
            delivery_method=delivery_method,
        )
        return {
            "id": schedule.id,
            "schedule_name": schedule.schedule_name,
            "frequency": schedule.frequency,
            "next_run_at": schedule.next_run_at,
            "created_at": schedule.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/schedules/due")
async def get_due_schedules(db: Session = Depends(get_db)):
    """Get schedules due for execution"""
    schedules = ReportScheduleService.get_schedules_due_for_execution(db)
    return {
        "schedules": [s.to_dict() for s in schedules],
        "count": len(schedules),
    }


@app.get("/schedules/user/{user_id}")
async def get_user_schedules(
    user_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get schedules for a user"""
    schedules, total = ReportScheduleService.get_user_schedules(
        db, user_id, limit, offset
    )
    return {
        "schedules": [s.to_dict() for s in schedules],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.patch("/schedules/{schedule_id}/execute")
async def mark_schedule_executed(
    schedule_id: int,
    success: bool = True,
    db: Session = Depends(get_db),
):
    """Mark schedule as executed"""
    schedule = ReportScheduleService.update_schedule_after_execution(db, schedule_id, success)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {
        "next_run_at": schedule.next_run_at,
        "run_count": schedule.run_count,
    }


# ============================================================================
# REPORT EXPORT ENDPOINTS
# ============================================================================


@app.post("/exports", status_code=201)
async def create_export(
    report_id: int,
    export_format: str,
    file_path: str,
    file_size: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Create an export"""
    try:
        # Validate report exists
        report = ReportGenerationService.get_report(db, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        export = ReportExportService.create_export(
            db=db,
            report_id=report_id,
            export_format=export_format,
            file_path=file_path,
            file_size=file_size,
        )
        return {
            "id": export.id,
            "export_format": export.export_format,
            "export_status": export.export_status,
            "created_at": export.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/exports/report/{report_id}")
async def get_report_exports(
    report_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get exports for a report"""
    exports, total = ReportExportService.get_report_exports(db, report_id, limit, offset)
    return {
        "exports": [e.to_dict() for e in exports],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.patch("/exports/{export_id}/download")
async def record_export_download(export_id: int, db: Session = Depends(get_db)):
    """Record an export download"""
    export = ReportExportService.record_download(db, export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    return {
        "download_count": export.download_count,
        "last_downloaded_at": export.last_downloaded_at,
    }


# ============================================================================
# REPORT METRICS ENDPOINTS
# ============================================================================


@app.post("/metrics", status_code=201)
async def record_metric(
    report_id: int,
    metric_name: str,
    metric_value: float,
    metric_unit: str,
    metric_category: str = "performance",
    db: Session = Depends(get_db),
):
    """Record a metric"""
    try:
        metric = ReportMetricsService.record_metric(
            db=db,
            report_id=report_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            metric_category=metric_category,
        )
        return {
            "id": metric.id,
            "metric_name": metric.metric_name,
            "metric_value": metric.metric_value,
            "recorded_at": metric.recorded_at,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/metrics/report/{report_id}")
async def get_report_metrics(
    report_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get metrics for a report"""
    metrics, total = ReportMetricsService.get_report_metrics(db, report_id, limit, offset)
    return {
        "metrics": [m.to_dict() for m in metrics],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/metrics/category/{category}")
async def get_metrics_by_category(
    category: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get metrics by category"""
    metrics, total = ReportMetricsService.get_metrics_by_category(
        db, category, limit, offset
    )
    return {
        "metrics": [m.to_dict() for m in metrics],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/metrics/average/{metric_name}")
async def get_average_metrics(
    metric_name: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get average metrics over time period"""
    stats = ReportMetricsService.get_average_metrics(db, metric_name, days)
    return {
        "metric_name": metric_name,
        "period_days": days,
        **stats,
    }


# ============================================================================
# REPORT ACCESS LOGGING ENDPOINTS
# ============================================================================


@app.post("/access-logs", status_code=201)
async def log_report_access(
    report_id: int,
    user_id: int,
    access_type: str,
    access_status: str = "success",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    error_message: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Log report access"""
    try:
        log = ReportAccessService.log_access(
            db=db,
            report_id=report_id,
            user_id=user_id,
            access_type=access_type,
            access_status=access_status,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
            duration_seconds=duration_seconds,
        )
        return {
            "id": log.id,
            "access_type": log.access_type,
            "access_status": log.access_status,
            "accessed_at": log.accessed_at,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/access-logs/report/{report_id}")
async def get_report_access_logs(
    report_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get access logs for a report"""
    logs, total = ReportAccessService.get_report_access_logs(db, report_id, limit, offset)
    return {
        "logs": [l.to_dict() for l in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/access-logs/user/{user_id}")
async def get_user_access_logs(
    user_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get access logs for a user"""
    logs, total = ReportAccessService.get_user_access_logs(db, user_id, limit, offset)
    return {
        "logs": [l.to_dict() for l in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/access-logs/report/{report_id}/stats")
async def get_access_statistics(report_id: int, db: Session = Depends(get_db)):
    """Get access statistics for a report"""
    stats = ReportAccessService.get_access_statistics(db, report_id)
    return stats


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "reporting-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Reporting Service",
        "version": "1.0.0",
        "endpoints": {
            "templates": "/templates",
            "reports": "/reports",
            "schedules": "/schedules",
            "exports": "/exports",
            "metrics": "/metrics",
            "access_logs": "/access-logs",
            "health": "/health",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
