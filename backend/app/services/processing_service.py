from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Union

from app.services.analytics.engine import analyze_dataset
from app.services.analytics_service import calculate_summary_metrics, monthly_summary
from app.services.database_service import DatabaseService
from app.services.domain_service import detect_domain
from app.services.excel_service import build_dataframe, clean_records, read_excel_records
from app.services.openrouter_service import detect_domain_ai
from app.services.validation_service import ValidationResult, validate_records

logger = logging.getLogger(__name__)

# OpenRouter is called in a thread — if it doesn't finish within this budget,
# we skip it and fall back to local domain detection so the upload still succeeds.
# Keep well under gunicorn's 180s: excel parse + DB insert + AI budget < 180s
_AI_TIMEOUT_SECONDS = 40


def _ai_detect_with_timeout(
    column_names: list[str],
    cleaned_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run detect_domain_ai in a thread. Returns fallback dict on timeout or error."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(detect_domain_ai, column_names, cleaned_records)
        try:
            return future.result(timeout=_AI_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            logger.warning("OpenRouter timed out after %ss — using local domain detection.", _AI_TIMEOUT_SECONDS)
            future.cancel()
            return {
                "domain": "Generic",
                "confidence": 0,
                "reason": "AI timed out — local detection used.",
                "visualizations": [],
                "computed_charts": [],
                "computed_kpis": {},
                "kpis": [],
                "insights": [],
                "ai_powered": False,
                "error": "timeout",
            }
        except Exception as exc:
            logger.warning("OpenRouter failed: %s — using local domain detection.", exc)
            return {
                "domain": "Generic",
                "confidence": 0,
                "reason": f"AI failed: {exc}",
                "visualizations": [],
                "computed_charts": [],
                "computed_kpis": {},
                "kpis": [],
                "insights": [],
                "ai_powered": False,
                "error": str(exc),
            }


def _ai_detect_with_timeout(
    column_names: list[str],
    cleaned_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run detect_domain_ai in a thread. Returns fallback dict on timeout or error."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(detect_domain_ai, column_names, cleaned_records)
        try:
            return future.result(timeout=_AI_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            logger.warning("OpenRouter timed out after %ss — using local domain detection.", _AI_TIMEOUT_SECONDS)
            future.cancel()
            return {
                "domain": "Generic",
                "confidence": 0,
                "reason": "AI timed out — local detection used.",
                "visualizations": [],
                "computed_charts": [],
                "computed_kpis": {},
                "kpis": [],
                "insights": [],
                "ai_powered": False,
                "error": "timeout",
            }
        except Exception as exc:
            logger.warning("OpenRouter failed: %s — using local domain detection.", exc)
            return {
                "domain": "Generic",
                "confidence": 0,
                "reason": f"AI failed: {exc}",
                "visualizations": [],
                "computed_charts": [],
                "computed_kpis": {},
                "kpis": [],
                "insights": [],
                "ai_powered": False,
                "error": str(exc),
            }


@dataclass(slots=True)
class ProcessingResult:
    file_name: str
    domain_name: str
    confidence: float
    validation: ValidationResult
    upload_id: int | None
    row_count: int
    summary: dict[str, object]
    columns: list[str]


def process_excel_file(
    file_path: Union[str, Path, BytesIO],
    file_name: str,
    database_service: DatabaseService | None,
    cleaned_folder: str | Path | None = None,
    user_id: int | None = None,
) -> ProcessingResult:
    import time
    t0 = time.monotonic()

    records = read_excel_records(file_path)
    logger.info("[%s] read_excel: %.2fs, %d rows", file_name, time.monotonic() - t0, len(records))

    column_names = list(records[0].keys()) if records else []
    validation = validate_records(records, column_names)
    cleaned_records = clean_records(records)
    logger.info("[%s] clean+validate: %.2fs", file_name, time.monotonic() - t0)

    # Run OpenRouter AI in a thread with a hard timeout — never blocks upload
    t_ai = time.monotonic()
    ai_result = _ai_detect_with_timeout(column_names, cleaned_records)
    logger.info("[%s] ai_detect: %.2fs (ai_powered=%s)", file_name, time.monotonic() - t_ai, ai_result.get("ai_powered"))

    if ai_result.get("ai_powered") and ai_result.get("confidence", 0) >= 50:
        domain_name = ai_result["domain"]
        confidence = ai_result["confidence"] / 100.0
    else:
        domain_name, confidence = detect_domain(column_names, sample_records=cleaned_records)

    t_eng = time.monotonic()
    analytics_engine = analyze_dataset(cleaned_records)
    logger.info("[%s] analytics_engine: %.2fs", file_name, time.monotonic() - t_eng)

    summary = calculate_summary_metrics(cleaned_records)

    date_column = next((column for column in column_names if column.lower().endswith("date")), None)
    summary["monthly_summary"] = (
        monthly_summary([str(record.get(date_column)) for record in cleaned_records if date_column and record.get(date_column)])
        if date_column
        else {}
    )
    summary["detected_domain"] = analytics_engine["domain"]["name"]
    summary["domain_confidence"] = analytics_engine["domain"]["confidence"]
    summary["analytics_engine"] = analytics_engine
    summary["kpis"] = analytics_engine.get("kpis", {})
    summary["charts"] = analytics_engine.get("charts", {})
    summary["insights"] = analytics_engine.get("insights", [])
    summary["ai_result"] = ai_result

    # Only attempt to write cleaned file if folder is provided and writable.
    if cleaned_folder is not None:
        try:
            cleaned_path = Path(cleaned_folder)
            cleaned_path.mkdir(parents=True, exist_ok=True)
            cleaned_file_path = cleaned_path / f"{Path(file_name).stem}_cleaned.xlsx"
            build_dataframe(cleaned_records).to_excel(cleaned_file_path, index=False)
        except OSError as exc:
            logger.warning("Could not write cleaned file (read-only filesystem?): %s", exc)

    upload_id = None
    if database_service is not None and validation.is_valid:
        t_db = time.monotonic()

        # Store a lean summary — only what the dashboard endpoint reads.
        # Storing full analytics_engine + ai_result was megabytes per upload
        # and made insert_upload very slow on Neon.
        lean_summary: dict[str, object] = {
            "total_rows": summary.get("total_rows", len(cleaned_records)),
            "average_numeric_value": summary.get("average_numeric_value", 0),
            "monthly_summary": summary.get("monthly_summary", {}),
            "detected_domain": summary.get("detected_domain", domain_name),
            "domain_confidence": summary.get("domain_confidence", confidence),
        }

        # Keep analytics_engine charts/kpis (small, used by dashboard)
        eng = summary.get("analytics_engine", {})
        if isinstance(eng, dict):
            lean_summary["analytics_engine"] = {
                "domain": eng.get("domain", {}),
                "row_count": eng.get("row_count", 0),
                "column_count": eng.get("column_count", 0),
                "kpis": eng.get("kpis", {}),
                "charts": eng.get("charts", {}),
                "insights": eng.get("insights", []),
            }

        # Keep ai_result but strip the full computed_charts values list to save space
        ai = summary.get("ai_result", {})
        if isinstance(ai, dict) and ai.get("ai_powered"):
            lean_summary["ai_result"] = {
                "ai_powered": True,
                "domain": ai.get("domain"),
                "confidence": ai.get("confidence"),
                "insights": ai.get("insights", []),
                "computed_kpis": ai.get("computed_kpis", {}),
                # Keep computed_charts but cap labels/values at 20 entries each
                "computed_charts": [
                    {**c, "labels": c.get("labels", [])[:20], "values": c.get("values", [])[:20]}
                    for c in (ai.get("computed_charts") or [])[:4]
                ],
            }
        else:
            lean_summary["ai_result"] = ai

        upload_id = database_service.insert_upload(
            file_name=file_name,
            domain_name=domain_name,
            confidence=confidence,
            row_count=len(cleaned_records),
            summary=lean_summary,
            user_id=user_id,
        )
        database_service.insert_rows(upload_id, cleaned_records)
        logger.info("[%s] db_insert: %.2fs (%d rows)", file_name, time.monotonic() - t_db, len(cleaned_records))

    logger.info("[%s] TOTAL: %.2fs", file_name, time.monotonic() - t0)

    return ProcessingResult(
        file_name=file_name,
        domain_name=domain_name,
        confidence=confidence,
        validation=validation,
        upload_id=upload_id,
        row_count=len(cleaned_records),
        summary=summary,
        columns=column_names,
    )