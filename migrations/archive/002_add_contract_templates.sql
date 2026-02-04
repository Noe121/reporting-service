-- Reporting Service Migration: Add Contract Report Templates
-- Migration: 002_add_contract_templates.sql
-- Purpose: Add report templates for contract signing analytics and compliance

USE reporting_db;

-- Insert contract-related report templates
INSERT INTO report_templates (
    template_name,
    template_type,
    description,
    sections,
    export_formats,
    parameters,
    is_default,
    is_active
) VALUES
-- Contract Signing Report
(
    'Contract Signing Report',
    'contracts',
    'Comprehensive contract signing analytics including completion rates, timing metrics, and participant statistics',
    '[
        "executive_summary",
        "signing_volume",
        "completion_rates",
        "average_signing_duration",
        "participant_analysis",
        "template_usage",
        "failure_analysis",
        "trends"
    ]',
    '["pdf", "xlsx", "csv", "json"]',
    '{
        "date_range": "required",
        "group_by": ["day", "week", "month"],
        "filters": {
            "template_id": "optional",
            "status": "optional",
            "source_type": "optional"
        }
    }',
    FALSE,
    TRUE
),

-- Contract Performance Report
(
    'Contract Performance Report',
    'contracts',
    'Performance metrics for contract execution including signing speed, drop-off analysis, and bottleneck identification',
    '[
        "overview",
        "signing_funnel",
        "time_to_sign_by_role",
        "abandonment_analysis",
        "bottleneck_identification",
        "improvement_recommendations"
    ]',
    '["pdf", "xlsx"]',
    '{
        "date_range": "required",
        "comparison_period": "optional",
        "filters": {
            "template_id": "optional",
            "participant_role": "optional"
        }
    }',
    FALSE,
    TRUE
),

-- Contract Compliance Report
(
    'Contract Compliance Report',
    'compliance',
    'Compliance status of all signed contracts including NCAA rules, state regulations, and disclosure requirements',
    '[
        "compliance_summary",
        "violations_breakdown",
        "contracts_by_status",
        "disclosure_tracking",
        "audit_trail",
        "regulatory_updates"
    ]',
    '["pdf", "xlsx"]',
    '{
        "date_range": "required",
        "athlete_type": "optional",
        "state": "optional",
        "division": "optional"
    }',
    FALSE,
    TRUE
),

-- Daily Contract Activity Report
(
    'Daily Contract Activity Report',
    'contracts',
    'Daily summary of contract signing activity for operations monitoring',
    '[
        "daily_summary",
        "new_signings_initiated",
        "signings_completed",
        "signings_pending",
        "issues_flagged"
    ]',
    '["pdf", "csv", "json"]',
    '{
        "date": "required"
    }',
    FALSE,
    TRUE
),

-- Contract Template Usage Report
(
    'Contract Template Usage Report',
    'contracts',
    'Analysis of contract template usage patterns and effectiveness',
    '[
        "template_overview",
        "usage_by_template",
        "completion_rate_by_template",
        "average_duration_by_template",
        "template_recommendations"
    ]',
    '["pdf", "xlsx", "csv"]',
    '{
        "date_range": "required",
        "include_archived": "optional"
    }',
    FALSE,
    TRUE
),

-- Contract Revenue Impact Report
(
    'Contract Revenue Impact Report',
    'financial',
    'Financial impact analysis of signed contracts including deal values and revenue attribution',
    '[
        "revenue_summary",
        "contracts_by_value",
        "signing_to_revenue_timeline",
        "payment_correlation",
        "forecasting"
    ]',
    '["pdf", "xlsx"]',
    '{
        "date_range": "required",
        "currency": "USD",
        "filters": {
            "min_value": "optional",
            "max_value": "optional",
            "brand_id": "optional"
        }
    }',
    FALSE,
    TRUE
);

-- Add contract-specific metric categories
-- These will be tracked via the event consumer

-- Verification
SELECT 'Contract report templates added successfully' as status;
SELECT template_name, template_type, is_active FROM report_templates WHERE template_type IN ('contracts', 'compliance');
