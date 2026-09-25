
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.dependencies import get_db
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.academic_class import AcademicClass
from backend.app.models.department import Department
from backend.app.models.user import User


@pytest.fixture
def assignment_api_environment():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        department = Department(
            name="Information Technology",
            code="IT",
        )
        db.add(department)
        db.flush()

        academic_class = AcademicClass(
            department_id=department.id,
            name="IT",
            section="A",
            semester=5,
        )
        db.add(academic_class)

        users = [
            User(
                login_id="assignment_admin",
                full_name="Assignment Admin",
                password_hash=hash_password("AdminTestPassword123"),
                role="ADMIN",
                is_active=True,
                must_change_password=False,
            ),
            User(
                login_id="assignment_teacher_one",
                full_name="Teacher One",
                password_hash=hash_password("TeacherTestPassword123"),
                role="TEACHER",
                is_active=True,
                must_change_password=False,
            ),
            User(
                login_id="assignment_teacher_two",
                full_name="Teacher Two",
                password_hash=hash_password("TeacherTestPassword123"),
                role="TEACHER",
                is_active=True,
                must_change_password=False,
            ),
            User(
                login_id="assignment_student",
                full_name="Assignment Student",
                password_hash=hash_password("StudentTestPassword123"),
                role="STUDENT",
                is_active=True,
                must_change_password=False,
            ),
        ]

        db.add_all(users)
        db.commit()

        class_id = academic_class.id
        teacher_one_id = users[1].id
        teacher_two_id = users[2].id

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield (
                client,
                class_id,
                teacher_one_id,
                teacher_two_id,
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def login(client, login_id, password):
    response = client.post(
        "/api/auth/login",
        json={
            "login_id": login_id,
            "password": password,
        },
    )

    assert response.status_code == 200

    return {
        "Authorization": (
            f"Bearer {response.json()['access_token']}"
        )
    }


def test_admin_creates_teacher_assignment(
    assignment_api_environment,
):
    client, class_id, teacher_id, _ = (
        assignment_api_environment
    )

    admin_headers = login(
        client,
        "assignment_admin",
        "AdminTestPassword123",
    )

    response = client.post(
        "/api/teacher-assignments/",
        headers=admin_headers,
        json={
            "teacher_id": teacher_id,
            "academic_class_id": class_id,
        },
    )

    assert response.status_code == 201
    assert response.json()["teacher_id"] == teacher_id
    assert response.json()["academic_class_id"] == class_id

    duplicate = client.post(
        "/api/teacher-assignments/",
        headers=admin_headers,
        json={
            "teacher_id": teacher_id,
            "academic_class_id": class_id,
        },
    )

    assert duplicate.status_code == 409


def test_teacher_sees_only_own_assignments(
    assignment_api_environment,
):
    client, class_id, teacher_one_id, teacher_two_id = (
        assignment_api_environment
    )

    admin_headers = login(
        client,
        "assignment_admin",
        "AdminTestPassword123",
    )

    for teacher_id in (
        teacher_one_id,
        teacher_two_id,
    ):
        response = client.post(
            "/api/teacher-assignments/",
            headers=admin_headers,
            json={
                "teacher_id": teacher_id,
                "academic_class_id": class_id,
            },
        )

        assert response.status_code == 201

    teacher_headers = login(
        client,
        "assignment_teacher_one",
        "TeacherTestPassword123",
    )

    response = client.get(
        "/api/teacher-assignments/me",
        headers=teacher_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["teacher_id"] == teacher_one_id

    all_assignments = client.get(
        "/api/teacher-assignments/",
        headers=admin_headers,
    )

    assert all_assignments.status_code == 200
    assert len(all_assignments.json()) == 2


def test_assignment_access_control(
    assignment_api_environment,
):
    client, class_id, teacher_id, _ = (
        assignment_api_environment
    )

    student_headers = login(
        client,
        "assignment_student",
        "StudentTestPassword123",
    )

    teacher_headers = login(
        client,
        "assignment_teacher_one",
        "TeacherTestPassword123",
    )

    payload = {
        "teacher_id": teacher_id,
        "academic_class_id": class_id,
    }

    assert client.post(
        "/api/teacher-assignments/",
        json=payload,
    ).status_code == 401

    assert client.post(
        "/api/teacher-assignments/",
        headers=student_headers,
        json=payload,
    ).status_code == 403

    assert client.post(
        "/api/teacher-assignments/",
        headers=teacher_headers,
        json=payload,
    ).status_code == 403

    assert client.get(
        "/api/teacher-assignments/",
        headers=teacher_headers,
    ).status_code == 403

    assert client.get(
        "/api/teacher-assignments/me",
        headers=student_headers,
    ).status_code == 403
