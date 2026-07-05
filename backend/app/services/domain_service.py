from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable


# ---------------------------------------------------------------------------
# Keyword sets — column name fragments (substring match, case-insensitive)
# ---------------------------------------------------------------------------
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "Placement Management": [
        "candidate", "placement", "interview", "offer", "campus",
        "ctc", "joining", "recruit", "drive", "company", "applied",
        "selected", "hired", "package", "passout", "batch", "cgpa",
        "resume", "shortlist", "intern", "graduate", "college",
    ],
    "HR Management": [
        "employee", "emp", "department", "dept", "designation",
        "salary", "leave", "attendance", "hr", "staff", "workforce",
        "payroll", "appraisal", "manager", "gender", "hire_date",
        "joining", "experience", "grade", "division", "headcount",
    ],
    "Retail Sales": [
        "sale", "revenue", "customer", "order", "invoice", "discount",
        "amount", "retail", "product", "item", "quantity", "price",
        "purchase", "vendor", "store", "bill", "transaction", "payment",
        "receipt", "total", "tax", "profit",
    ],
    "Inventory": [
        "inventory", "stock", "sku", "warehouse", "reorder", "qty",
        "product", "supplier", "batch", "expiry", "unit", "shelf",
        "bin", "category", "available", "threshold", "lead_time",
    ],
    "Student Attendance": [
        "attendance", "present", "absent", "checkin", "checkout",
        "shift", "late", "class", "subject", "student", "roll",
        "period", "session", "section", "semester", "course",
        "mark", "faculty", "lecture",
    ],
}

# Row-value patterns per domain (checked against cell values sampled from the data)
DOMAIN_VALUE_PATTERNS: dict[str, list[str]] = {
    "Placement Management": [
        "placed", "selected", "hired", "offer", "campus", "drive",
        "intern", "fresher", "mba", "btech", "mtech", "engineering",
    ],
    "HR Management": [
        "male", "female", "active", "resigned", "terminated", "full.?time",
        "part.?time", "hr", "manager", "director", "executive", "associate",
    ],
    "Retail Sales": [
        r"\$", "paid", "pending", "shipped", "delivered", "cancelled",
        "online", "offline", "cash", "card", "upi",
    ],
    "Inventory": [
        "in.?stock", "out.?of.?stock", "low.?stock", "kg", "litre",
        "pcs", "units", "box", "carton", "warehouse",
    ],
    "Student Attendance": [
        r"^p$", r"^a$", "present", "absent", "late", r"\d{2}/\d{2}/\d{4}",
    ],
}

GENERIC_DOMAIN = "Generic"
_DETECT_THRESHOLD = 0.06  # minimum score to claim a specific domain


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", " ", text.lower()).strip()


def _column_score(normalized_columns: list[str], keywords: list[str]) -> float:
    """Score based on how many keywords appear as substrings in column names."""
    hits = sum(
        1
        for kw in keywords
        if any(kw in col for col in normalized_columns)
    )
    return hits / max(len(keywords), 1)


def _value_score(sample_values: list[str], patterns: list[str]) -> float:
    """Score based on how many value-patterns appear in sampled cell values."""
    if not sample_values:
        return 0.0
    hits = 0
    for pattern in patterns:
        compiled = re.compile(pattern, re.IGNORECASE)
        if any(compiled.search(v) for v in sample_values):
            hits += 1
    return hits / max(len(patterns), 1)


def detect_domain(
    column_names: Iterable[str],
    sample_records: list[dict[str, object]] | None = None,
) -> tuple[str, float]:
    """Return (domain_name, confidence_0_to_1).

    Combines column-name keyword matching with value-pattern sampling for
    much more robust domain detection on real-world Excel files.
    """
    cols = [_normalize(c) for c in column_names]
    if not cols:
        return GENERIC_DOMAIN, 0.0

    # Sample up to 200 cell values for value-pattern scoring
    sample_values: list[str] = []
    if sample_records:
        for record in sample_records[:200]:
            for v in record.values():
                if v is not None and str(v).strip():
                    sample_values.append(str(v).strip())

    scores: dict[str, float] = {}
    for domain_name, keywords in DOMAIN_KEYWORDS.items():
        col_s = _column_score(cols, keywords)
        val_s = 0.0
        if sample_values:
            val_s = _value_score(sample_values, DOMAIN_VALUE_PATTERNS.get(domain_name, []))
        # Weighted combination: column names matter more
        combined = col_s * 0.70 + val_s * 0.30
        scores[domain_name] = round(combined, 4)

    best_domain = max(scores, key=lambda d: scores[d])
    best_score = scores[best_domain]

    if best_score < _DETECT_THRESHOLD:
        # Still return the best guess with actual score instead of hard-coding 0
        return GENERIC_DOMAIN, round(best_score, 4)

    return best_domain, round(best_score, 2)