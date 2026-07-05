from __future__ import annotations

from pathlib import Path
from uuid import uuid4


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in allowed_extensions


def generate_storage_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{uuid4().hex}{suffix}"


def ensure_directories(*directory_paths: str | Path) -> None:
    for directory_path in directory_paths:
        Path(directory_path).mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file, destination_folder: str | Path) -> Path:
    ensure_directories(destination_folder)
    storage_name = generate_storage_name(uploaded_file.filename)
    destination_path = Path(destination_folder) / storage_name
    uploaded_file.save(destination_path)
    return destination_path