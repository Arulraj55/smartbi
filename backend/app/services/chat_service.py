from __future__ import annotations

import json
from app.services.database_service import DatabaseService
from app.services.openrouter_service import _call_openrouter


def chat_with_dataset(upload_id: int, user_message: str, database_service: DatabaseService) -> str:
    upload = database_service.fetch_upload_by_id(upload_id)
    if upload is None:
        raise ValueError("Dataset upload not found.")

    rows = database_service.fetch_upload_rows(upload_id)
    
    # Sample up to 15 rows to provide concrete examples without blowing up context window
    sample_rows = [{k: str(v)[:60] for k, v in row.items()} for row in rows[:15]]
    column_names = list(rows[0].keys()) if rows else []
    
    summary_json = upload.get("summary_json") or {}
    kpis = summary_json.get("kpis", {})
    domain_name = upload.get("domain_name", "Generic")

    prompt = f"""You are SmartBI AI, a helpful Business Intelligence data assistant.
Analyze the dataset information below and answer the user's question.

### Dataset Metadata
- File Name: {upload.get("file_name")}
- Domain: {domain_name}
- Total Rows: {upload.get("row_count")}
- Available Columns/Fields: {column_names}

### Calculated KPIs
{json.dumps(kpis, indent=2)}

### Sample Rows (First 15 rows)
{json.dumps(sample_rows, indent=2)}

### User Question
{user_message}

### Instructions
- Respond directly, concisely, and professionally to the user's question.
- Do not repeat the sample rows or KPIs unnecessarily.
- Base your answers strictly on the provided data context.
- Use markdown formatting (like tables, bullet points, bold text, or code formatting) where appropriate to make the answer clear and readable.
- If the question cannot be answered from the provided sample or KPIs, explain what is missing.
"""
    try:
        response = _call_openrouter(prompt)
        return response
    except Exception as exc:
        return f"I ran into an issue analyzing the data: {str(exc)}"
