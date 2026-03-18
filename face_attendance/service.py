from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from face_attendance.config import (
    DEFAULT_DETECTOR,
    DEFAULT_DISTANCE_METRIC,
    DEFAULT_MODEL_NAME,
    KNOWN_FACES_DIR,
)
from face_attendance.storage import (
    AttendanceRecord,
    append_attendance_record,
    attendance_already_marked,
    ensure_project_directories,
    list_registered_people,
    read_display_name,
)


try:
    import cv2
except ImportError:  # pragma: no cover - depends on local environment
    cv2 = None

try:
    from deepface import DeepFace
except ImportError:  # pragma: no cover - depends on local environment
    DeepFace = None


@dataclass
class RecognitionMatch:
    person_name: str
    identity: str
    distance: float
    threshold: float | str
    face_index: int
    facial_area: dict[str, Any]


@dataclass
class MarkAttendanceResult:
    match: RecognitionMatch
    status: str
    timestamp: str


class FaceAttendanceService:
    def __init__(
        self,
        db_path: Path = KNOWN_FACES_DIR,
        model_name: str = DEFAULT_MODEL_NAME,
        detector_backend: str = DEFAULT_DETECTOR,
        distance_metric: str = DEFAULT_DISTANCE_METRIC,
    ) -> None:
        self.db_path = db_path
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric

    def recognize(self, image_source: Any) -> list[RecognitionMatch]:
        self._ensure_runtime_dependencies()
        ensure_project_directories()

        if not list_registered_people():
            raise RuntimeError(
                "No hay rostros registrados. Usa el comando 'register' antes de reconocer."
            )

        raw_results = DeepFace.find(
            img_path=image_source,
            db_path=str(self.db_path),
            model_name=self.model_name,
            detector_backend=self.detector_backend,
            distance_metric=self.distance_metric,
            enforce_detection=False,
            silent=True,
        )

        dataframes = raw_results if isinstance(raw_results, list) else [raw_results]
        matches: list[RecognitionMatch] = []

        for face_index, dataframe in enumerate(dataframes):
            if dataframe.empty:
                continue

            distance_column = self._resolve_distance_column(dataframe)
            best_row = dataframe.sort_values(distance_column).iloc[0]
            identity = str(best_row["identity"])
            person_name = read_display_name(Path(identity).parent)
            threshold = best_row.get("threshold", "")
            facial_area = {
                "x": self._safe_int(best_row.get("source_x")),
                "y": self._safe_int(best_row.get("source_y")),
                "w": self._safe_int(best_row.get("source_w")),
                "h": self._safe_int(best_row.get("source_h")),
            }

            matches.append(
                RecognitionMatch(
                    person_name=person_name,
                    identity=identity,
                    distance=float(best_row[distance_column]),
                    threshold=threshold,
                    face_index=face_index,
                    facial_area=facial_area,
                )
            )

        return matches

    def mark_attendance(self, image_source: Any, source_label: str) -> list[MarkAttendanceResult]:
        matches = self.recognize(image_source)
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().isoformat(timespec="seconds")
        results: list[MarkAttendanceResult] = []

        for match in matches:
            if attendance_already_marked(match.person_name, today):
                status = "duplicado"
            else:
                status = "registrado"
                append_attendance_record(
                    AttendanceRecord(
                        person_name=match.person_name,
                        timestamp=timestamp,
                        source=source_label,
                        distance=round(match.distance, 6),
                        threshold=match.threshold,
                        status=status,
                    )
                )

            results.append(MarkAttendanceResult(match=match, status=status, timestamp=timestamp))

        return results

    def analyze_image(self, image_source: Any) -> list[dict[str, Any]]:
        self._ensure_runtime_dependencies()
        results = DeepFace.analyze(
            img_path=image_source,
            actions=("age", "gender", "emotion"),
            detector_backend=self.detector_backend,
            enforce_detection=False,
            silent=True,
        )
        return results if isinstance(results, list) else [results]

    def run_webcam_attendance(self, camera_index: int = 0, frame_interval: int = 30) -> None:
        self._ensure_runtime_dependencies(require_opencv=True)
        capture = cv2.VideoCapture(camera_index)

        if not capture.isOpened():
            raise RuntimeError(f"No se pudo abrir la camara con indice {camera_index}.")

        print("Presiona 'q' para salir.")
        frame_number = 0
        last_labels: list[str] = []

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("No se pudo leer un frame de la camara.")

                frame_number += 1

                if frame_number % max(frame_interval, 1) == 0:
                    results = self.mark_attendance(frame, source_label=f"webcam:{camera_index}")
                    last_labels = [
                        f"{result.match.person_name} [{result.status}]"
                        for result in results
                    ] or ["Sin coincidencias"]

                    for result in results:
                        print(
                            f"[{result.status}] {result.match.person_name} "
                            f"(distance={result.match.distance:.4f})"
                        )

                for index, label in enumerate(last_labels):
                    cv2.putText(
                        frame,
                        label,
                        (20, 40 + (index * 30)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )

                cv2.imshow("Asistencia facial", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
        finally:
            capture.release()
            cv2.destroyAllWindows()

    def _ensure_runtime_dependencies(self, require_opencv: bool = False) -> None:
        missing: list[str] = []
        if DeepFace is None:
            missing.append("deepface")
        if require_opencv and cv2 is None:
            missing.append("opencv-python")

        if missing:
            missing_str = ", ".join(missing)
            raise RuntimeError(
                "Faltan dependencias para ejecutar el proyecto: "
                f"{missing_str}. Instala requirements.txt en un entorno virtual."
            )

    def _resolve_distance_column(self, dataframe: Any) -> str:
        for candidate in dataframe.columns:
            if "distance" in str(candidate).lower():
                return str(candidate)

        numeric_columns = [
            column
            for column in dataframe.columns
            if str(getattr(dataframe[column], "dtype", "")).startswith(("float", "int"))
        ]
        if numeric_columns:
            return str(numeric_columns[0])

        raise RuntimeError("No se encontro una columna de distancia en los resultados de DeepFace.")

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
