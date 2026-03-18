from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from face_attendance.config import (
    ATTENDANCE_CSV,
    CAPTURES_DIR,
    KNOWN_FACES_DIR,
    REPORTS_DIR,
    SUPPORTED_IMAGE_EXTENSIONS,
)


@dataclass
class AttendanceRecord:
    person_name: str
    timestamp: str
    source: str
    distance: float
    threshold: float | str
    status: str


def ensure_project_directories() -> None:
    KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)


def slugify_person_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    return cleaned.strip("_") or "persona"


def person_directory(name: str) -> Path:
    return KNOWN_FACES_DIR / slugify_person_name(name)


def display_name_from_slug(slug: str) -> str:
    return slug.replace("_", " ").strip().title()


def read_display_name(person_dir: str | Path) -> str:
    directory = Path(person_dir)
    profile_path = directory / "profile.json"

    if profile_path.exists():
        with profile_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
            display_name = str(payload.get("display_name", "")).strip()
            if display_name:
                return display_name

    return display_name_from_slug(directory.name)


def register_face_image(name: str, image_path: str | Path) -> Path:
    ensure_project_directories()
    source_path = Path(image_path).expanduser().resolve()

    if not source_path.exists():
        raise FileNotFoundError(f"No se encontro la imagen: {source_path}")

    if source_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        raise ValueError(f"Formato de imagen no soportado. Usa uno de: {allowed}")

    destination_dir = person_directory(name)
    destination_dir.mkdir(parents=True, exist_ok=True)
    profile_path = destination_dir / "profile.json"
    profile_path.write_text(
        json.dumps({"display_name": name.strip()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination_path = destination_dir / f"{timestamp}_{source_path.name}"
    shutil.copy2(source_path, destination_path)
    return destination_path


def list_registered_people() -> list[str]:
    ensure_project_directories()
    people = [read_display_name(path) for path in KNOWN_FACES_DIR.iterdir() if path.is_dir()]
    return sorted(people)


def attendance_already_marked(person_name: str, date_str: str) -> bool:
    if not ATTENDANCE_CSV.exists():
        return False

    with ATTENDANCE_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["person_name"] == person_name and row["timestamp"].startswith(date_str):
                return True
    return False


def append_attendance_record(record: AttendanceRecord) -> None:
    ensure_project_directories()
    fieldnames = list(asdict(record).keys())
    file_exists = ATTENDANCE_CSV.exists()

    with ATTENDANCE_CSV.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(asdict(record))


def read_attendance_records() -> list[dict[str, str]]:
    if not ATTENDANCE_CSV.exists():
        return []

    with ATTENDANCE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def attendance_summary(date_str: str | None = None) -> list[dict[str, str]]:
    records = read_attendance_records()
    if not date_str:
        return records
    return [row for row in records if row["timestamp"].startswith(date_str)]
