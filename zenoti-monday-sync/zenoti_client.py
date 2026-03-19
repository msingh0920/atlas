"""Zenoti API client for pulling appointments, sales, and membership data."""

import requests
from datetime import datetime, timedelta
from dateutil import parser as dateparser


class ZenotiClient:
    def __init__(self, api_key, base_url="https://api.zenoti.com/v1"):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"apikey {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint, payload=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # -------------------------------------------------------------------------
    # Appointments
    # -------------------------------------------------------------------------

    def get_appointments(self, center_id, start_date, end_date, status=None):
        """Pull appointments for a center within a date range.

        Status codes:
            1  = Confirmed
            2  = Checked-in
            4  = Completed
           -1  = Cancelled
           -2  = No-show (note: Zenoti hides no-shows from most endpoints)
        """
        params = {
            "center_id": center_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        if status is not None:
            params["status"] = status

        data = self._get("/appointments", params)
        return data.get("appointments", [])

    def get_appointment_metrics(self, center_id, start_date, end_date):
        """Calculate appointment completion, cancellation, and no-show rates."""
        appointments = self.get_appointments(center_id, start_date, end_date)

        metrics = {
            "total": len(appointments),
            "completed": 0,
            "confirmed": 0,
            "checked_in": 0,
            "cancelled": 0,
            "no_show": 0,
            "by_service": {},
        }

        for appt in appointments:
            status = appt.get("appointment_group", {}).get("status", 0)
            service_name = (
                appt.get("services", [{}])[0].get("service", {}).get("name", "Unknown")
                if appt.get("services")
                else "Unknown"
            )

            if status == 4:
                metrics["completed"] += 1
            elif status == 1:
                metrics["confirmed"] += 1
            elif status == 2:
                metrics["checked_in"] += 1
            elif status == -1:
                metrics["cancelled"] += 1
            elif status == -2:
                metrics["no_show"] += 1
                # Note: Zenoti hides no-show details; service_name may be unavailable
                service_name = "Unknown (No-Show)"

            metrics["by_service"].setdefault(service_name, 0)
            metrics["by_service"][service_name] += 1

        if metrics["total"] > 0:
            metrics["completion_rate"] = round(
                metrics["completed"] / metrics["total"] * 100, 1
            )
            metrics["no_show_rate"] = round(
                metrics["no_show"] / metrics["total"] * 100, 1
            )
            metrics["cancellation_rate"] = round(
                metrics["cancelled"] / metrics["total"] * 100, 1
            )
        else:
            metrics["completion_rate"] = 0
            metrics["no_show_rate"] = 0
            metrics["cancellation_rate"] = 0

        return metrics

    # -------------------------------------------------------------------------
    # Sales / Collections
    # -------------------------------------------------------------------------

    def get_sales(self, center_id, start_date, end_date):
        """Pull sales/collection data for a center."""
        payload = {
            "center_id": center_id,
            "start_date": start_date.strftime("%Y-%m-%dT00:00:00"),
            "end_date": end_date.strftime("%Y-%m-%dT23:59:59"),
        }
        data = self._post("/reports/sales", payload)
        return data

    def get_revenue_breakdown(self, center_id, start_date, end_date):
        """Parse sales data into revenue by service line."""
        sales_data = self.get_sales(center_id, start_date, end_date)

        breakdown = {
            "total_revenue": 0,
            "by_service_line": {},
            "by_payment_method": {},
            "transaction_count": 0,
        }

        for item in sales_data.get("sales", []):
            amount = item.get("total", {}).get("amount", 0)
            service = item.get("item_name", "Other")
            payment = item.get("payment_type", "Unknown")

            breakdown["total_revenue"] += amount
            breakdown["transaction_count"] += 1

            breakdown["by_service_line"].setdefault(service, 0)
            breakdown["by_service_line"][service] += amount

            breakdown["by_payment_method"].setdefault(payment, 0)
            breakdown["by_payment_method"][payment] += amount

        breakdown["total_revenue"] = round(breakdown["total_revenue"], 2)

        return breakdown

    # -------------------------------------------------------------------------
    # Memberships
    # -------------------------------------------------------------------------

    def get_memberships(self, center_id, status=None):
        """Pull membership data. Status: active, frozen, cancelled, expired."""
        params = {"center_id": center_id}
        if status:
            params["status"] = status

        data = self._get("/members", params)
        return data.get("members", [])

    def get_membership_metrics(self, center_id):
        """Calculate membership status breakdown."""
        metrics = {
            "active": 0,
            "frozen": 0,
            "cancelled": 0,
            "expired": 0,
            "total": 0,
            "by_plan": {},
        }

        for status_key in ["active", "frozen", "cancelled", "expired"]:
            members = self.get_memberships(center_id, status=status_key)
            count = len(members)
            metrics[status_key] = count
            metrics["total"] += count

            for member in members:
                plan = member.get("membership", {}).get("name", "Unknown Plan")
                metrics["by_plan"].setdefault(plan, {"active": 0, "frozen": 0, "cancelled": 0, "expired": 0})
                metrics["by_plan"][plan][status_key] += 1

        return metrics

    # -------------------------------------------------------------------------
    # Aggregation
    # -------------------------------------------------------------------------

    def pull_daily_report(self, center_ids, date=None):
        """Pull all metrics for all centers for a given date.

        Args:
            center_ids: dict of {location_name: center_id}
            date: date to pull (defaults to yesterday)

        Returns:
            dict with per-location and combined metrics
        """
        if date is None:
            date = datetime.now().date() - timedelta(days=1)

        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())

        report = {
            "date": date.isoformat(),
            "locations": {},
            "combined": {
                "appointments": {},
                "revenue": {},
                "memberships": {},
            },
        }

        for location, cid in center_ids.items():
            loc_data = {
                "appointments": self.get_appointment_metrics(cid, start, end),
                "revenue": self.get_revenue_breakdown(cid, start, end),
                "memberships": self.get_membership_metrics(cid),
            }
            report["locations"][location] = loc_data

        # Combine totals across locations
        combined_appts = {"total": 0, "completed": 0, "no_show": 0, "cancelled": 0}
        combined_rev = {"total_revenue": 0, "transaction_count": 0}
        combined_members = {"active": 0, "frozen": 0, "cancelled": 0, "expired": 0}

        for loc_data in report["locations"].values():
            for key in combined_appts:
                combined_appts[key] += loc_data["appointments"].get(key, 0)
            combined_rev["total_revenue"] += loc_data["revenue"].get("total_revenue", 0)
            combined_rev["transaction_count"] += loc_data["revenue"].get("transaction_count", 0)
            for key in combined_members:
                combined_members[key] += loc_data["memberships"].get(key, 0)

        if combined_appts["total"] > 0:
            combined_appts["completion_rate"] = round(
                combined_appts["completed"] / combined_appts["total"] * 100, 1
            )
            combined_appts["no_show_rate"] = round(
                combined_appts["no_show"] / combined_appts["total"] * 100, 1
            )

        report["combined"]["appointments"] = combined_appts
        report["combined"]["revenue"] = combined_rev
        report["combined"]["memberships"] = combined_members

        return report
