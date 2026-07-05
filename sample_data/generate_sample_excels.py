from __future__ import annotations

from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parent / "generated"


def write_excel(file_name: str, rows: list[dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_excel(OUTPUT_DIR / file_name, index=False)


def main() -> None:
    write_excel(
        "placement_sample.xlsx",
        [
            {"Candidate Name": "Asha Nair", "College": "ABC Engineering", "Company": "TechNova", "Interview Date": "2026-01-05", "Offer CTC": 12.5, "Status": "Selected"},
            {"Candidate Name": "Ravi Kumar", "College": "XYZ Institute", "Company": "FinEdge", "Interview Date": "2026-01-12", "Offer CTC": 9.0, "Status": "On Hold"},
            {"Candidate Name": "Meera Joshi", "College": "PQR University", "Company": "CloudPeak", "Interview Date": "2026-02-03", "Offer CTC": 14.2, "Status": "Selected"},
        ],
    )

    write_excel(
        "hr_sample.xlsx",
        [
            {"Employee Name": "Isha Sharma", "Department": "Finance", "Designation": "Analyst", "Salary": 68000, "Joining Date": "2026-01-02", "Leave Balance": 12, "Status": "Active"},
            {"Employee Name": "Naveen Patil", "Department": "Sales", "Designation": "Manager", "Salary": 98000, "Joining Date": "2026-02-01", "Leave Balance": 9, "Status": "Active"},
            {"Employee Name": "Karan Rao", "Department": "HR", "Designation": "Executive", "Salary": 62000, "Joining Date": "2026-02-18", "Leave Balance": 15, "Status": "Active"},
        ],
    )

    write_excel(
        "retail_sales_sample.xlsx",
        [
            {"Order ID": "ORD-1001", "Customer Name": "City Mart", "Order Date": "2026-01-08", "Product": "Laptop", "Amount": 85000, "Region": "West"},
            {"Order ID": "ORD-1002", "Customer Name": "Fresh Basket", "Order Date": "2026-01-16", "Product": "Tablet", "Amount": 24000, "Region": "South"},
            {"Order ID": "ORD-1003", "Customer Name": "Tech World", "Order Date": "2026-02-11", "Product": "Monitor", "Amount": 18000, "Region": "North"},
        ],
    )

    write_excel(
        "inventory_sample.xlsx",
        [
            {"SKU": "SKU-001", "Product Name": "Laptop", "Category": "Electronics", "Stock Qty": 42, "Reorder Level": 10, "Warehouse": "WH-A"},
            {"SKU": "SKU-002", "Product Name": "Mouse", "Category": "Accessories", "Stock Qty": 180, "Reorder Level": 40, "Warehouse": "WH-B"},
            {"SKU": "SKU-003", "Product Name": "Keyboard", "Category": "Accessories", "Stock Qty": 75, "Reorder Level": 20, "Warehouse": "WH-A"},
        ],
    )

    write_excel(
        "attendance_sample.xlsx",
        [
            {"Employee Name": "Asha Nair", "Attendance Date": "2026-01-05", "Check In": "09:05", "Check Out": "18:02", "Status": "Present", "Shift": "General"},
            {"Employee Name": "Ravi Kumar", "Attendance Date": "2026-01-06", "Check In": "09:20", "Check Out": "17:58", "Status": "Late", "Shift": "General"},
            {"Employee Name": "Meera Joshi", "Attendance Date": "2026-01-07", "Check In": "08:55", "Check Out": "18:10", "Status": "Present", "Shift": "General"},
        ],
    )


if __name__ == "__main__":
    main()