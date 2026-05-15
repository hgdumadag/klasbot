from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from klasbot import db


SCORE_DISTRIBUTION = [0.58, 0.66, 0.72, 0.76, 0.79, 0.82, 0.85, 0.88, 0.93, 0.97]


SAMPLE_CLASSES = [
    {
        "name": "Grade 6 - Science",
        "grade_level": "6",
        "section": "A",
        "subject": "Science",
        "school_year": "2026-2027",
        "students": [
            ("Ana", "Santos"),
            ("Ben", "Reyes"),
            ("Cara", "Lim"),
            ("Dina", "Cruz"),
            ("Enzo", "Garcia"),
            ("Faith", "Mendoza"),
            ("Gio", "Dela Cruz"),
            ("Hannah", "Torres"),
            ("Ivan", "Ramos"),
            ("Jasmine", "Navarro"),
        ],
        "assessments": [
            ("Quiz 1: Matter and Its Properties", "quiz", "2026-04-02", 20),
            ("Performance Task: Simple Investigation", "performance_task", "2026-04-24", 30),
            ("Unit Test: Force, Motion, and Energy", "exam", "2026-05-08", 50),
        ],
    },
    {
        "name": "Grade 5 - Mathematics",
        "grade_level": "5",
        "section": "B",
        "subject": "Mathematics",
        "school_year": "2026-2027",
        "students": [
            ("Karla", "Villanueva"),
            ("Liam", "Aquino"),
            ("Mia", "Flores"),
            ("Noah", "Bautista"),
            ("Olivia", "Castillo"),
            ("Paolo", "Rivera"),
            ("Queenie", "Morales"),
            ("Rafael", "Domingo"),
            ("Sofia", "Cabrera"),
            ("Theo", "Salazar"),
        ],
        "assessments": [
            ("Quiz 1: Fractions and Decimals", "quiz", "2026-04-03", 20),
            ("Assignment: Problem Solving Set", "assignment", "2026-04-25", 25),
            ("Unit Test: Number Patterns", "exam", "2026-05-09", 50),
        ],
    },
    {
        "name": "Grade 4 - English",
        "grade_level": "4",
        "section": "C",
        "subject": "English",
        "school_year": "2026-2027",
        "students": [
            ("Alyssa", "Manalo"),
            ("Bryan", "Ocampo"),
            ("Chloe", "Padilla"),
            ("Diego", "Soriano"),
            ("Ella", "Tan"),
            ("Francis", "Uy"),
            ("Gabrielle", "Valdez"),
            ("Harvey", "Yap"),
            ("Isabella", "Zamora"),
            ("Joshua", "Pascual"),
        ],
        "assessments": [
            ("Quiz 1: Context Clues", "quiz", "2026-04-06", 20),
            ("Performance Task: Short Oral Reading", "performance_task", "2026-04-27", 30),
            ("Unit Test: Reading Comprehension", "exam", "2026-05-10", 50),
        ],
    },
    {
        "name": "Grade 3 - Filipino",
        "grade_level": "3",
        "section": "D",
        "subject": "Filipino",
        "school_year": "2026-2027",
        "students": [
            ("Kiara", "Abad"),
            ("Luis", "Bernardo"),
            ("Mara", "Concepcion"),
            ("Nico", "David"),
            ("Patricia", "Evangelista"),
            ("Rico", "Francisco"),
            ("Sam", "Gonzales"),
            ("Tala", "Hernandez"),
            ("Uma", "Ignacio"),
            ("Vince", "Jimenez"),
        ],
        "assessments": [
            ("Maikling Pagsusulit: Pangngalan", "quiz", "2026-04-07", 20),
            ("Gawain: Pagbasa at Pagsagot", "performance_task", "2026-04-28", 30),
            ("Pangwakas na Pagsusulit: Pag-unawa", "exam", "2026-05-08", 50),
        ],
    },
]


def find_teacher(teacher_id: int | None) -> dict:
    teachers = db.list_teachers()
    if teacher_id is not None:
        for teacher in teachers:
            if int(teacher["id"]) == teacher_id:
                return teacher
        raise SystemExit(f"No teacher found with id {teacher_id}.")
    if not teachers:
        raise SystemExit("No teachers found. Run scripts/seed_admin.py first.")
    admins = [teacher for teacher in teachers if teacher.get("is_admin")]
    return admins[0] if admins else teachers[0]


def find_existing_class(teacher_id: int, sample: dict) -> dict | None:
    for class_record in db.list_class_records(teacher_id):
        if (
            class_record["name"] == sample["name"]
            and class_record["grade_level"] == sample["grade_level"]
            and (class_record.get("section") or "") == sample["section"]
            and class_record["subject"] == sample["subject"]
        ):
            return class_record
    return None


def student_exists(students: list[dict], first_name: str, last_name: str) -> bool:
    return any(
        student["first_name"].casefold() == first_name.casefold()
        and student["last_name"].casefold() == last_name.casefold()
        for student in students
    )


def assessment_exists(
    assessments: list[dict],
    title: str,
    assessment_type: str,
    assessment_date: str,
) -> bool:
    return any(
        assessment["title"].casefold() == title.casefold()
        and assessment["assessment_type"] == assessment_type
        and assessment["assessment_date"] == assessment_date
        for assessment in assessments
    )


def bell_scores(max_score: float, count: int, offset: int = 0) -> list[float]:
    scores = [
        round(max_score * SCORE_DISTRIBUTION[(index + offset) % len(SCORE_DISTRIBUTION)], 2)
        for index in range(count)
    ]
    return sorted(scores)


def seed_assessment_scores(teacher_id: int, class_id: int) -> None:
    students = db.list_class_students(teacher_id, class_id) or []
    assessments = db.list_class_assessments(teacher_id, class_id) or []
    for assessment_index, assessment in enumerate(sorted(assessments, key=lambda item: item["assessment_date"])):
        scores = bell_scores(float(assessment["max_score"]), len(students), assessment_index)
        rows = []
        for student, score in zip(students, scores, strict=False):
            rows.append(
                {
                    "student_id": int(student["id"]),
                    "score": score,
                    "notes": "Sample bell distribution score",
                }
            )
        db.save_score_grid(teacher_id, int(assessment["id"]), rows)


def seed_sample_classes(teacher_id: int) -> list[dict]:
    seeded = []
    for sample in SAMPLE_CLASSES:
        class_record = find_existing_class(teacher_id, sample)
        if class_record is None:
            class_record = db.create_class_record(teacher_id, sample)

        current_students = db.list_class_students(teacher_id, int(class_record["id"])) or []
        for first_name, last_name in sample["students"]:
            if student_exists(current_students, first_name, last_name):
                continue
            student = db.create_or_enroll_student(
                teacher_id,
                int(class_record["id"]),
                {"first_name": first_name, "last_name": last_name},
            )
            if student:
                current_students.append(student)

        current_assessments = db.list_class_assessments(teacher_id, int(class_record["id"])) or []
        for title, assessment_type, assessment_date, max_score in sample["assessments"]:
            if assessment_exists(current_assessments, title, assessment_type, assessment_date):
                continue
            assessment = db.create_assessment(
                teacher_id,
                int(class_record["id"]),
                {
                    "title": title,
                    "assessment_type": assessment_type,
                    "assessment_date": assessment_date,
                    "max_score": max_score,
                    "notes": "Sample assessment",
                },
            )
            if assessment:
                current_assessments.append(assessment)

        seed_assessment_scores(teacher_id, int(class_record["id"]))

        class_record = db.get_class_record(teacher_id, int(class_record["id"])) or class_record
        seeded.append(class_record)
    return seeded


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed four sample class records with students.")
    parser.add_argument("--teacher-id", type=int, help="Teacher id to own the sample classes")
    args = parser.parse_args()

    db.init_db()
    teacher = find_teacher(args.teacher_id)
    seeded = seed_sample_classes(int(teacher["id"]))
    print(f"Seeded sample classes for teacher #{teacher['id']}: {teacher['name']}")
    for class_record in seeded:
        print(
            f"- {class_record['name']} ({class_record['subject']}): "
            f"{class_record['student_count']} students, "
            f"{len(db.list_class_assessments(int(teacher['id']), int(class_record['id'])) or [])} assessments"
        )


if __name__ == "__main__":
    main()
