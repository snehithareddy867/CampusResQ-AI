"""Helping-team availability using existing users.available + active incidents."""
from typing import Dict, List, Optional

ACTIVE_ASSIGNED = {"accepted", "en_route", "arrived"}


def evaluate_team_availability(
    responders: List[dict],
    active_assigned_ids: Optional[set] = None,
) -> Dict:
    """
    responders: users with role=responder in the routed department.
    active_assigned_ids: user ids currently handling an accepted/en_route/arrived incident.
    """
    active_assigned_ids = active_assigned_ids or set()
    total = len(responders)
    if total == 0:
        return {
            "state": "unavailable",
            "reason": "team_not_found",
            "total_members": 0,
            "available_member_count": 0,
            "idle_members": [],
        }

    flagged_on = [r for r in responders if r.get("available") is not False]
    idle = [r for r in flagged_on if r.get("id") not in active_assigned_ids]

    if idle:
        return {
            "state": "available",
            "reason": "members_idle",
            "total_members": total,
            "available_member_count": len(idle),
            "idle_members": idle,
        }
    if flagged_on:
        return {
            "state": "busy",
            "reason": "all_available_members_busy",
            "total_members": total,
            "available_member_count": 0,
            "idle_members": [],
        }
    return {
        "state": "offline",
        "reason": "all_members_offline",
        "total_members": total,
        "available_member_count": 0,
        "idle_members": [],
    }
