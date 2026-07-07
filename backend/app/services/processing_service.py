from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Union

from app.services.analytics.engine import analyze_dataset
from app.services.analytics_service import calculate_summary_metrics, monthly_summary
from app.services.database_service import DatabaseService
from app.services.domain_service import detect_domain
from app.services.excel_service import build_dataframe, clean_records, read_excel_records
from app.services.openrouter_service import detect_domain_ai
from app.services.validation_service import ValidationResult, validate_records

logger = logging.getLogger(__name__)


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
    records = read_excel_records(file_path)
    column_names = list(records[0].keys()) if records else []
    validation = validate_records(records, column_names)
    cleaned_records = clean_records(records)

    # Use OpenRouter AI for domain detection and visualization decisions
    ai_result = detect_domain_ai(column_names, cleaned_records)

    if ai_result.get("ai_powered") and ai_result.get("confidence", 0) >= 50:
        domain_name = ai_result["domain"]
        confidence = ai_result["confidence"] / 100.0
    else:
        domain_name, confidence = detect_domain(column_names, sample_records=cleaned_records)

    analytics_engine = analyze_dataset(cleaned_records)
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
    # On read-only/ephemeral filesystems (e.g. Render) this is skipped gracefully.
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
        upload_id = database_service.insert_upload(
            file_name=file_name,
            domain_name=domain_name,
            confidence=confidence,
            row_count=len(cleaned_records),
            summary=summary,
            user_id=user_id,
        )
        database_service.insert_rows(upload_id, cleaned_records)

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