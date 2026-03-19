"""Monday.com API client for creating boards and pushing Zenoti report data."""

import json
import requests


MONDAY_API_URL = "https://api.monday.com/v2"


class MondayClient:
    def __init__(self, api_key):
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }

    def _query(self, query, variables=None):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = requests.post(
            MONDAY_API_URL, headers=self.headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise Exception(f"Monday.com API error: {result['errors']}")
        return result.get("data", {})

    # -------------------------------------------------------------------------
    # Board Setup
    # -------------------------------------------------------------------------

    def create_report_board(self, board_name="Zenoti Daily Report"):
        """Create a new board with columns for all report metrics."""
        query = """
        mutation ($name: String!) {
            create_board(board_name: $name, board_kind: private) {
                id
            }
        }
        """
        data = self._query(query, {"name": board_name})
        board_id = data["create_board"]["id"]

        columns = [
            ("location", "Location", "text"),
            ("report_date", "Report Date", "date"),
            # Appointment metrics
            ("appt_total", "Appointments Total", "numbers"),
            ("appt_completed", "Completed", "numbers"),
            ("appt_no_show", "No-Shows", "numbers"),
            ("appt_cancelled", "Cancelled", "numbers"),
            ("appt_completion_rate", "Completion Rate %", "numbers"),
            ("appt_no_show_rate", "No-Show Rate %", "numbers"),
            ("appt_cancel_rate", "Cancellation Rate %", "numbers"),
            # Revenue metrics
            ("rev_total", "Total Revenue", "numbers"),
            ("rev_transactions", "Transaction Count", "numbers"),
            ("rev_by_service", "Revenue by Service", "long_text"),
            # Membership metrics
            ("mem_active", "Active Members", "numbers"),
            ("mem_frozen", "Frozen", "numbers"),
            ("mem_cancelled", "Cancelled Members", "numbers"),
            ("mem_expired", "Expired", "numbers"),
            ("mem_by_plan", "Members by Plan", "long_text"),
            # Top services
            ("top_services", "Top Services (Appts)", "long_text"),
        ]

        for col_id, title, col_type in columns:
            col_query = """
            mutation ($board_id: ID!, $title: String!, $column_type: ColumnType!, $id: String) {
                create_column(board_id: $board_id, title: $title, column_type: $column_type, id: $id) {
                    id
                }
            }
            """
            self._query(col_query, {
                "board_id": board_id,
                "title": title,
                "column_type": col_type,
                "id": col_id,
            })

        return board_id

    def get_board_items(self, board_id):
        """Get all items on a board."""
        query = """
        query ($board_id: ID!) {
            boards(ids: [$board_id]) {
                items_page(limit: 500) {
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                        }
                    }
                }
            }
        }
        """
        data = self._query(query, {"board_id": board_id})
        boards = data.get("boards", [])
        if boards:
            return boards[0].get("items_page", {}).get("items", [])
        return []

    # -------------------------------------------------------------------------
    # Push Report Data
    # -------------------------------------------------------------------------

    def push_report(self, board_id, report):
        """Push a full Zenoti daily report to Monday.com board.

        Creates one row per location + one combined row.
        Updates existing rows if they match date + location.
        """
        date_str = report["date"]

        # Push per-location rows
        for location, loc_data in report["locations"].items():
            self._upsert_report_row(board_id, date_str, location, loc_data)

        # Push combined row
        if len(report["locations"]) > 1:
            combined_data = {
                "appointments": report["combined"]["appointments"],
                "revenue": report["combined"]["revenue"],
                "memberships": report["combined"]["memberships"],
            }
            self._upsert_report_row(board_id, date_str, "All Locations", combined_data)

    def _upsert_report_row(self, board_id, date_str, location, data):
        """Create or update a row for a specific date + location."""
        appts = data.get("appointments", {})
        rev = data.get("revenue", {})
        mem = data.get("memberships", {})

        # Format top services
        by_service = appts.get("by_service", {})
        top_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:10]
        top_services_text = "\n".join(f"{name}: {count}" for name, count in top_services)

        # Format revenue by service
        rev_by_service = rev.get("by_service_line", {})
        rev_sorted = sorted(rev_by_service.items(), key=lambda x: x[1], reverse=True)[:10]
        rev_text = "\n".join(f"{name}: ${amt:,.2f}" for name, amt in rev_sorted)

        # Format members by plan
        by_plan = mem.get("by_plan", {})
        plan_lines = []
        for plan, statuses in by_plan.items():
            active = statuses.get("active", 0)
            plan_lines.append(f"{plan}: {active} active")
        plan_text = "\n".join(plan_lines[:10])

        column_values = {
            "location": location,
            "report_date": {"date": date_str},
            "appt_total": appts.get("total", 0),
            "appt_completed": appts.get("completed", 0),
            "appt_no_show": appts.get("no_show", 0),
            "appt_cancelled": appts.get("cancelled", 0),
            "appt_completion_rate": appts.get("completion_rate", 0),
            "appt_no_show_rate": appts.get("no_show_rate", 0),
            "appt_cancel_rate": appts.get("cancellation_rate", 0),
            "rev_total": rev.get("total_revenue", 0),
            "rev_transactions": rev.get("transaction_count", 0),
            "rev_by_service": {"text": rev_text},
            "mem_active": mem.get("active", 0),
            "mem_frozen": mem.get("frozen", 0),
            "mem_cancelled": mem.get("cancelled", 0),
            "mem_expired": mem.get("expired", 0),
            "mem_by_plan": {"text": plan_text},
            "top_services": {"text": top_services_text},
        }

        item_name = f"{location} — {date_str}"

        # Check for existing item with same name
        existing = self._find_item_by_name(board_id, item_name)

        if existing:
            self._update_item(board_id, existing["id"], column_values)
        else:
            self._create_item(board_id, item_name, column_values)

    def _find_item_by_name(self, board_id, name):
        """Find an existing item by name."""
        items = self.get_board_items(board_id)
        for item in items:
            if item["name"] == name:
                return item
        return None

    def _create_item(self, board_id, name, column_values):
        """Create a new item on the board."""
        query = """
        mutation ($board_id: ID!, $name: String!, $column_values: JSON!) {
            create_item(board_id: $board_id, item_name: $name, column_values: $column_values) {
                id
            }
        }
        """
        self._query(query, {
            "board_id": board_id,
            "name": name,
            "column_values": json.dumps(column_values),
        })

    def _update_item(self, board_id, item_id, column_values):
        """Update an existing item's column values."""
        query = """
        mutation ($board_id: ID!, $item_id: ID!, $column_values: JSON!) {
            change_multiple_column_values(board_id: $board_id, item_id: $item_id, column_values: $column_values) {
                id
            }
        }
        """
        self._query(query, {
            "board_id": board_id,
            "item_id": item_id,
            "column_values": json.dumps(column_values),
        })
