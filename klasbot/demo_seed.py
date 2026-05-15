from __future__ import annotations

from pathlib import Path

from klasbot import curriculum, db
from klasbot.auth import hash_pin
from klasbot.config import PROJECT_ROOT


SAMPLE_ATTENDANCE_DATES = [
    "2026-04-27",
    "2026-04-28",
    "2026-04-29",
    "2026-04-30",
    "2026-05-01",
    "2026-05-04",
    "2026-05-05",
    "2026-05-06",
    "2026-05-07",
    "2026-05-08",
    "2026-05-11",
    "2026-05-12",
    "2026-05-13",
    "2026-05-14",
    "2026-05-15",
]


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
            ("Fatima", "Mendoza"),
            ("Gab", "Torres"),
            ("Hannah", "Navarro"),
            ("Ivan", "Delos Reyes"),
            ("Jessa", "Ramos"),
        ],
        "assessments": [
            ("Quiz 1: Matter and Its Properties", "quiz", "2026-04-02", 20),
            ("Performance Task: Simple Investigation", "performance_task", "2026-04-24", 30),
            ("Unit Test: Earth Systems", "exam", "2026-05-10", 50),
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
            ("Paolo", "Dizon"),
            ("Queenie", "Mercado"),
            ("Rafael", "Soriano"),
            ("Sofia", "Magtibay"),
            ("Theo", "Valdez"),
        ],
        "assessments": [
            ("Quiz 1: Fractions and Decimals", "quiz", "2026-04-03", 20),
            ("Unit Test: Number Patterns", "exam", "2026-05-09", 50),
            ("Performance Task: Market Day Budget", "performance_task", "2026-05-23", 30),
        ],
    },
    {
        "name": "Grade 4 - English",
        "grade_level": "4",
        "section": "C",
        "subject": "English",
        "school_year": "2026-2027",
        "students": [
            ("Aira", "Manalo"),
            ("Bryan", "Ocampo"),
            ("Celine", "Pascual"),
            ("Daniel", "Rivera"),
            ("Ella", "Salazar"),
            ("Francis", "Tan"),
            ("Gian", "Uy"),
            ("Hazel", "Vergara"),
            ("Isabel", "Yap"),
            ("Joshua", "Zamora"),
        ],
        "assessments": [
            ("Reading Check: Main Idea and Details", "quiz", "2026-04-05", 15),
            ("Writing Task: Friendly Letter", "performance_task", "2026-04-26", 25),
            ("Quarter Test: Reading and Language", "exam", "2026-05-11", 40),
        ],
    },
    {
        "name": "Grade 7 - Araling Panlipunan",
        "grade_level": "7",
        "section": "D",
        "subject": "Araling Panlipunan",
        "school_year": "2026-2027",
        "students": [
            ("Adrian", "Abad"),
            ("Bianca", "Agustin"),
            ("Carlos", "Alcantara"),
            ("Denise", "Alonzo"),
            ("Emilio", "Andrada"),
            ("Faye", "Angeles"),
            ("Gino", "Apostol"),
            ("Heidi", "Arceo"),
            ("Ian", "Austria"),
            ("Janelle", "Bacani"),
            ("Kevin", "Balagtas"),
            ("Lara", "Balingit"),
            ("Marco", "Barrera"),
            ("Nina", "Basilio"),
            ("Oscar", "Belmonte"),
            ("Patricia", "Bernardo"),
            ("Quinn", "Buenaventura"),
            ("Rico", "Cabrera"),
            ("Sam", "Calderon"),
            ("Trixie", "Camacho"),
            ("Ulises", "Carpio"),
            ("Vera", "Catapang"),
            ("Warren", "Cayetano"),
            ("Xandra", "Concepcion"),
            ("Yuri", "Corpuz"),
            ("Zara", "David"),
            ("Althea", "Domingo"),
            ("Brent", "Dumlao"),
            ("Cheska", "Espina"),
            ("Diego", "Estrella"),
            ("Elise", "Fajardo"),
            ("Felix", "Francisco"),
            ("Gail", "Gatchalian"),
            ("Harvey", "Gomez"),
            ("Iris", "Guerrero"),
            ("Jonas", "Hernandez"),
            ("Kaye", "Ignacio"),
            ("Luis", "Jacinto"),
            ("Mara", "Lacson"),
            ("Nico", "Magno"),
        ],
        "assessments": [
            ("Map Skills Quiz: Regions of the Philippines", "quiz", "2026-04-06", 25),
            ("Performance Task: Community Timeline", "performance_task", "2026-04-28", 35),
            ("Unit Test: Philippine Geography and Culture", "exam", "2026-05-12", 60),
        ],
    },
]


def seed_demo_data(admin_name: str, admin_pin: str, *, include_curriculum: bool = True) -> dict:
    teacher = _ensure_demo_admin(admin_name, admin_pin)
    classes = _seed_sample_classes(int(teacher["id"]))
    documents = _seed_curriculum_json() if include_curriculum else db.list_curriculum_documents()
    return {"teacher": teacher, "classes": classes, "curriculum_documents": documents}


def _ensure_demo_admin(admin_name: str, admin_pin: str) -> dict:
    for teacher in db.list_teachers():
        if teacher["name"].casefold() == admin_name.casefold():
            return teacher
    return db.create_teacher(admin_name, hash_pin(admin_pin), is_admin=True)


def _seed_sample_classes(teacher_id: int) -> list[dict]:
    seeded = []
    for sample in SAMPLE_CLASSES:
        class_record = _find_existing_class(teacher_id, sample)
        if class_record is None:
            class_record = db.create_class_record(teacher_id, sample)
        class_id = int(class_record["id"])
        _seed_students(teacher_id, class_id, sample["students"])
        _seed_assessments(teacher_id, class_id, sample["assessments"])
        _seed_scores(teacher_id, class_id)
        _seed_attendance(teacher_id, class_id)
        seeded.append(db.get_class_record(teacher_id, class_id) or class_record)
    return seeded


def _find_existing_class(teacher_id: int, sample: dict) -> dict | None:
    for class_record in db.list_class_records(teacher_id):
        if (
            class_record["name"] == sample["name"]
            and class_record["grade_level"] == sample["grade_level"]
            and (class_record.get("section") or "") == sample["section"]
            and class_record["subject"] == sample["subject"]
        ):
            return class_record
    return None


def _seed_students(teacher_id: int, class_id: int, students: list[tuple[str, str]]) -> None:
    current_students = db.list_class_students(teacher_id, class_id) or []
    for first_name, last_name in students:
        if any(
            student["first_name"].casefold() == first_name.casefold()
            and student["last_name"].casefold() == last_name.casefold()
            for student in current_students
        ):
            continue
        student = db.create_or_enroll_student(
            teacher_id,
            class_id,
            {"first_name": first_name, "last_name": last_name},
        )
        if student:
            current_students.append(student)


def _seed_assessments(teacher_id: int, class_id: int, assessments: list[tuple[str, str, str, float]]) -> None:
    current_assessments = db.list_class_assessments(teacher_id, class_id) or []
    for title, assessment_type, assessment_date, max_score in assessments:
        if any(
            assessment["title"].casefold() == title.casefold()
            and assessment["assessment_type"] == assessment_type
            and assessment["assessment_date"] == assessment_date
            for assessment in current_assessments
        ):
            continue
        assessment = db.create_assessment(
            teacher_id,
            class_id,
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


def _seed_scores(teacher_id: int, class_id: int) -> None:
    students = db.list_class_students(teacher_id, class_id) or []
    assessments = db.list_class_assessments(teacher_id, class_id) or []
    for assessment_index, assessment in enumerate(assessments):
        rows = []
        for student_index, student in enumerate(students):
            max_score = float(assessment["max_score"])
            ratio = 0.68 + ((student_index + assessment_index) % 5) * 0.06
            rows.append(
                {
                    "student_id": int(student["id"]),
                    "score": round(min(max_score, max_score * ratio), 2),
                    "notes": "Sample demo score",
                }
            )
        db.save_score_grid(teacher_id, int(assessment["id"]), rows)


def _seed_attendance(teacher_id: int, class_id: int) -> None:
    students = db.list_class_students(teacher_id, class_id) or []
    if not students:
        return
    for date_index, attendance_date in enumerate(SAMPLE_ATTENDANCE_DATES):
        rows = []
        for student_index, student in enumerate(students):
            pattern = student_index + date_index
            status = "present"
            notes = "Sample attendance"
            if pattern % 23 == 0:
                status = "excused"
                notes = "Excused sample absence"
            elif pattern % 17 == 0:
                status = "absent"
                notes = "Sample absence"
            elif pattern % 11 == 0:
                status = "late"
                notes = "Sample late arrival"
            rows.append(
                {
                    "student_id": int(student["id"]),
                    "status": status,
                    "notes": notes,
                }
            )
        db.save_attendance_grid(teacher_id, class_id, attendance_date, rows)


def _seed_curriculum_json() -> list[dict]:
    if db.curriculum_grades():
        return db.list_curriculum_documents()
    for path in _curriculum_paths():
        curriculum.ingest_json(source_path=path)
    return db.list_curriculum_documents()


def _curriculum_paths() -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for curriculum_dir in _curriculum_dirs():
        if not curriculum_dir.exists():
            continue
        for path in sorted(curriculum_dir.glob("*.json")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(path)
    return paths


def _curriculum_dirs() -> list[Path]:
    roots = [
        Path(__file__).resolve().parent,
        PROJECT_ROOT,
        Path.cwd(),
        Path(__file__).resolve().parents[1],
        Path(__file__).resolve().parents[2],
    ]
    dirs: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        curriculum_dir = (root / "curriculum_json").resolve()
        if curriculum_dir in seen:
            continue
        seen.add(curriculum_dir)
        dirs.append(curriculum_dir)
    return dirs
