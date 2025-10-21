import io
from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from passes.models import Class, Enrollment, Submission, TeacherApplication, Profile, ProposedClass
from django.core import mail


@pytest.fixture
def roles(db):
    student_g, _ = Group.objects.get_or_create(name="student")
    teacher_g, _ = Group.objects.get_or_create(name="teacher")
    return student_g, teacher_g


@pytest.fixture
def users(db, roles):
    student = User.objects.create_user("student1", password="pass")
    teacher = User.objects.create_user("teacher1", password="pass")
    student.groups.add(roles[0])
    teacher.groups.add(roles[1])
    return student, teacher


@pytest.fixture
def course(db, users):
    _, teacher = users
    return Class.objects.create(
        name="Web App Development",
        teacher=teacher,
        year=1,
        deadline=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def enrolled_student(db, users, course):
    student, _ = users
    Enrollment.objects.create(student=student, class_ref=course)
    return student


def test_login_required(client):
    # home is public
    r = client.get(reverse("home"))
    assert r.status_code == 200
    # protected view should redirect to login
    r = client.get(reverse("submissions:list"))
    assert r.status_code in (302, 303)


@pytest.mark.django_db
def test_student_creates_submission(client, enrolled_student, course):
    client.login(username="student1", password="pass")
    file_bytes = io.BytesIO(b"hello world")
    upload = SimpleUploadedFile("assignment.txt", file_bytes.getvalue(), content_type="text/plain")

    r = client.post(
        reverse("submissions:new"),
        {"class_ref": course.id, "feedback": "my first try", "file": upload},
        format="multipart",
    )
    # redirect back to submissions list on success
    assert r.status_code in (302, 303)
    assert Submission.objects.filter(student=enrolled_student, class_ref=course).exists()


@pytest.mark.django_db
def test_teacher_approves_htmx(client, users, course, enrolled_student):
    # create a pending submission
    sub = Submission.objects.create(
        student=enrolled_student,
        class_ref=course,
        status="P",
        file=SimpleUploadedFile("work.txt", b"some content", content_type="text/plain"),
    )

    # teacher (who owns this class) approves via HTMX
    client.login(username="teacher1", password="pass")
    r = client.post(
        reverse("submissions:approve", args=[sub.id]),
        HTTP_HX_REQUEST="true",
    )
    assert r.status_code == 200
    sub.refresh_from_db()
    assert sub.status == "A"


@pytest.mark.django_db
def test_teacher_application_approval_creates_classes_and_enrolls():
    # Create a student with profile year 2
    student = User.objects.create_user("sally", password="pass")
    Profile.objects.create(user=student, student_year=2)
    # Prospective teacher
    teacher = User.objects.create_user("tom", password="pass")
    app = TeacherApplication.objects.create(
        user=teacher,
        is_teacher=True,
        course_names=["Intro to DB", "Algorithms I"],
        years=[2],
        status="P",
    )
    created = app.approve()
    assert len(created) == 2
    # Ensure enrollments for student in year 2 exist for each class
    for cls in created:
        assert Enrollment.objects.filter(student=student, class_ref=cls).exists()


@pytest.mark.django_db
def test_email_sent_on_teacher_application_creation(settings):
    settings.ADMINS = [("Admin", "admin@example.com")]
    teacher = User.objects.create_user("lucy", password="pass")
    TeacherApplication.objects.create(
        user=teacher,
        is_teacher=True,
        course_names=["Operating Systems"],
        years=[3],
        status="P",
    )
    # Using console backend, the email will appear in mail.outbox
    assert len(mail.outbox) == 1
    assert "teacher application" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
def test_proposed_class_approval_creates_class_and_enrolls():
    teacher = User.objects.create_user("teachx", password="pass")
    student = User.objects.create_user("studx", password="pass")
    Profile.objects.create(user=student, student_year=2)

    pc = ProposedClass.objects.create(teacher=teacher, name="Data Structures", year=2, status="P")
    cls = pc.approve()

    assert Class.objects.filter(id=cls.id, name="Data Structures", year=2, teacher=teacher).exists()
    assert Enrollment.objects.filter(student=student, class_ref=cls).exists()
