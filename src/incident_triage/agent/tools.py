from datetime import datetime
import random


def check_system_status(system_name: str) -> dict:
    """
    Check current operational status of a system.
    In production this calls a monitoring API (PagerDuty, Datadog, etc).
    Mock returns realistic status data for portfolio demonstration.

    Args:
        system_name: Name of the system to check

    Returns:
        dict with status, last_incident, response_time_ms, on_call
    """
    # Normalize system name
    system_key = system_name.lower().replace(" ", "_").replace("-", "_")

    # Mock system registry with realistic retail operations data
    system_registry = {
        "inventory_management_system": {
            "status": "degraded",
            "last_incident": "2026-05-19T03:00:00Z",
            "response_time_ms": 4200,
            "error_rate_pct": 12.4,
            "on_call": "platform-engineering-oncall@company.com",
            "runbook": "RUNBOOK-001",
        },
        "inventory_sync_job": {
            "status": "down",
            "last_incident": "2026-05-19T03:00:00Z",
            "response_time_ms": None,
            "error_rate_pct": 100.0,
            "on_call": "platform-engineering-oncall@company.com",
            "runbook": "RUNBOOK-001",
        },
        "replenishment_system": {
            "status": "degraded",
            "last_incident": "2026-05-19T03:15:00Z",
            "response_time_ms": 8900,
            "error_rate_pct": 34.2,
            "on_call": "platform-engineering-oncall@company.com",
            "runbook": "RUNBOOK-001",
        },
        "commodity_price_feed": {
            "status": "operational",
            "last_incident": "2026-05-17T06:00:00Z",
            "response_time_ms": 230,
            "error_rate_pct": 0.0,
            "on_call": "commodity-team-oncall@company.com",
            "runbook": "RUNBOOK-002",
        },
        "ml_forecasting_system": {
            "status": "operational",
            "last_incident": "2026-05-18T01:00:00Z",
            "response_time_ms": 1200,
            "error_rate_pct": 0.1,
            "on_call": "demand-forecast-oncall@company.com",
            "runbook": "RUNBOOK-003",
        },
        "data_warehouse": {
            "status": "operational",
            "last_incident": "2026-05-15T09:00:00Z",
            "response_time_ms": 450,
            "error_rate_pct": 0.0,
            "on_call": "platform-engineering-oncall@company.com",
            "runbook": "RUNBOOK-008",
        },
        "etl_pipeline": {
            "status": "operational",
            "last_incident": "2026-05-18T02:00:00Z",
            "response_time_ms": 320,
            "error_rate_pct": 0.2,
            "on_call": "platform-engineering-oncall@company.com",
            "runbook": "RUNBOOK-006",
        },
        "purchase_order_system": {
            "status": "operational",
            "last_incident": "2026-05-10T14:00:00Z",
            "response_time_ms": 180,
            "error_rate_pct": 0.0,
            "on_call": "platform-engineering-oncall@company.com",
            "runbook": "RUNBOOK-005",
        },
    }

    if system_key in system_registry:
        result = system_registry[system_key].copy()
        result["system"] = system_name
        result["checked_at"] = datetime.utcnow().isoformat() + "Z"
        return result

    # Unknown system — return unknown status
    return {
        "system": system_name,
        "status": "unknown",
        "message": f"System '{system_name}' not found in monitoring registry",
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }


def get_escalation_contacts(team: str) -> dict:
    """
    Get escalation contacts and procedures for a team.
    In production this queries a PagerDuty schedule or internal directory.
    Mock returns realistic on-call data.

    Args:
        team: Team name (platform_engineering, commodity_team, demand_forecast_team)

    Returns:
        dict with on_call contacts, escalation path, response SLA
    """
    team_key = team.lower().replace(" ", "_").replace("-", "_")

    escalation_registry = {
        "platform_engineering": {
            "team": "Platform Engineering",
            "primary_oncall": "Jane Smith",
            "primary_contact": "platform-engineering-oncall@company.com",
            "secondary_oncall": "Bob Johnson",
            "secondary_contact": "bob.johnson@company.com",
            "slack_channel": "#platform-incidents",
            "pagerduty_service": "platform-engineering",
            "response_sla_minutes": {
                "critical": 5,
                "high": 15,
                "medium": 60,
                "low": 240,
            },
            "escalation_path": [
                "1. Page primary on-call via PagerDuty",
                "2. If no response in 5 mins, page secondary on-call",
                "3. If no response in 10 mins, page Engineering Manager",
                "4. If no response in 15 mins, page VP Engineering",
            ],
            "war_room": "https://meet.company.com/platform-war-room",
        },
        "commodity_team": {
            "team": "Commodity Team",
            "primary_oncall": "Alice Chen",
            "primary_contact": "commodity-team-oncall@company.com",
            "secondary_oncall": "David Park",
            "secondary_contact": "david.park@company.com",
            "slack_channel": "#commodity-incidents",
            "pagerduty_service": "commodity-team",
            "response_sla_minutes": {
                "critical": 5,
                "high": 10,
                "medium": 30,
                "low": 120,
            },
            "escalation_path": [
                "1. Page primary on-call via PagerDuty",
                "2. Notify Commodity Trading desk immediately for critical",
                "3. If no response in 10 mins, page Commodity Team Lead",
                "4. Notify Finance for any purchase orders over $500k",
            ],
            "war_room": "https://meet.company.com/commodity-war-room",
        },
        "demand_forecast_team": {
            "team": "Demand Forecast Team",
            "primary_oncall": "Sarah Williams",
            "primary_contact": "demand-forecast-oncall@company.com",
            "secondary_oncall": "Michael Torres",
            "secondary_contact": "michael.torres@company.com",
            "slack_channel": "#forecast-incidents",
            "pagerduty_service": "demand-forecast",
            "response_sla_minutes": {
                "critical": 10,
                "high": 20,
                "medium": 60,
                "low": 480,
            },
            "escalation_path": [
                "1. Page primary on-call via PagerDuty",
                "2. Notify Replenishment team if orders are affected",
                "3. If no response in 15 mins, page Forecast Team Lead",
                "4. Pause automated replenishment if model confidence < 0.3",
            ],
            "war_room": "https://meet.company.com/forecast-war-room",
        },
    }

    if team_key in escalation_registry:
        result = escalation_registry[team_key].copy()
        result["checked_at"] = datetime.utcnow().isoformat() + "Z"
        return result

    return {
        "team": team,
        "status": "unknown",
        "message": f"Team '{team}' not found in escalation registry",
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }
