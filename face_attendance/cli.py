from __future__ import annotations

import argparse
from pathlib import Path

from face_attendance.config import ATTENDANCE_CSV, KNOWN_FACES_DIR
from face_attendance.service import FaceAttendanceService
from face_attendance.storage import (
    attendance_summary,
    ensure_project_directories,
    list_registered_people,
    register_face_image,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sistema de asistencia automatizada con reconocimiento facial usando DeepFace."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-dirs", help="Crea la estructura base del proyecto.")

    register_parser = subparsers.add_parser(
        "register", help="Registra la foto de una persona dentro de la base de rostros."
    )
    register_parser.add_argument("--name", required=True, help="Nombre de la persona.")
    register_parser.add_argument("--image", required=True, help="Ruta a la imagen a registrar.")

    subparsers.add_parser("list-people", help="Lista las personas registradas.")

    recognize_parser = subparsers.add_parser(
        "recognize", help="Reconoce los rostros encontrados en una imagen."
    )
    recognize_parser.add_argument("--image", required=True, help="Ruta a la imagen a analizar.")

    mark_parser = subparsers.add_parser(
        "mark", help="Marca asistencia usando una imagen de entrada."
    )
    mark_parser.add_argument("--image", required=True, help="Ruta a la imagen a analizar.")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analiza atributos faciales basicos (edad, genero y emocion dominante).",
    )
    analyze_parser.add_argument("--image", required=True, help="Ruta a la imagen a analizar.")

    report_parser = subparsers.add_parser(
        "report", help="Muestra el reporte de asistencia del dia o de una fecha especifica."
    )
    report_parser.add_argument(
        "--date",
        help="Fecha en formato YYYY-MM-DD. Si se omite, se muestran todos los registros.",
    )

    webcam_parser = subparsers.add_parser(
        "webcam", help="Abre la webcam y reconoce rostros en tiempo real."
    )
    webcam_parser.add_argument("--camera", type=int, default=0, help="Indice de la webcam.")
    webcam_parser.add_argument(
        "--frame-interval",
        type=int,
        default=30,
        help="Cada cuantos frames se ejecuta reconocimiento facial.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ensure_project_directories()
    service = FaceAttendanceService()

    try:
        if args.command == "init-dirs":
            print(f"Base de rostros: {KNOWN_FACES_DIR}")
            print(f"Reporte de asistencia: {ATTENDANCE_CSV}")
            return 0

        if args.command == "register":
            saved_path = register_face_image(args.name, args.image)
            print(f"Imagen registrada en: {saved_path}")
            return 0

        if args.command == "list-people":
            people = list_registered_people()
            if not people:
                print("No hay personas registradas.")
                return 0

            print("Personas registradas:")
            for person in people:
                print(f"- {person}")
            return 0

        if args.command == "recognize":
            matches = service.recognize(Path(args.image).expanduser().resolve())
            if not matches:
                print("No se encontraron coincidencias.")
                return 0

            for match in matches:
                print(
                    f"Rostro {match.face_index + 1}: {match.person_name} "
                    f"(distance={match.distance:.4f}, threshold={match.threshold})"
                )
            return 0

        if args.command == "mark":
            results = service.mark_attendance(
                Path(args.image).expanduser().resolve(),
                source_label=f"image:{Path(args.image).name}",
            )
            if not results:
                print("No se encontro ninguna persona registrada en la imagen.")
                return 0

            for result in results:
                print(
                    f"{result.match.person_name}: {result.status} "
                    f"(distance={result.match.distance:.4f})"
                )
            return 0

        if args.command == "analyze":
            analyses = service.analyze_image(Path(args.image).expanduser().resolve())
            for index, analysis in enumerate(analyses, start=1):
                dominant_gender = analysis.get("dominant_gender", "desconocido")
                dominant_emotion = analysis.get("dominant_emotion", "desconocida")
                age = analysis.get("age", "desconocida")
                print(
                    f"Rostro {index}: edad={age}, genero={dominant_gender}, "
                    f"emocion={dominant_emotion}"
                )
            return 0

        if args.command == "report":
            rows = attendance_summary(args.date)
            if not rows:
                print("No hay registros de asistencia para los criterios indicados.")
                return 0

            for row in rows:
                print(
                    f"{row['timestamp']} | {row['person_name']} | "
                    f"{row['status']} | {row['source']}"
                )
            return 0

        if args.command == "webcam":
            service.run_webcam_attendance(
                camera_index=args.camera,
                frame_interval=args.frame_interval,
            )
            return 0
    except Exception as exc:  # pragma: no cover - CLI level guard
        print(f"Error: {exc}")
        return 1

    parser.print_help()
    return 1
