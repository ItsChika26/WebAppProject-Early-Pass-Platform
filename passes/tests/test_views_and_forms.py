import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta

from passes.models import Class, Enrollment, ProposedClass
from passes.forms import ProposedClassForm


@pytest.mark.django_db
def test_class_list_filters_for_student(client):
    student = User.objects.create_user("stud", password="pass")
    Group.objects.get_or_create(name="student")[0].user_set.add(student)
    teacher = User.objects.create_user("teach", password="pass")

    c1 = Class.objects.create(name="Algebra", teacher=teacher, year=3, deadline=timezone.now()+timedelta(days=5))
    c2 = Class.objects.create(name="Biology", teacher=teacher, year=4, deadline=timezone.now()+timedelta(days=5))
    Enrollment.objects.create(student=student, class_ref=c1)

    client.login(username="stud", password="pass")

    # default shows only enrolled classes
    r = client.get(reverse("classes:list"))
    assert r.status_code == 200
    assert b"Algebra" in r.content and b"Biology" not in r.content

    # filter by q
    r = client.get(reverse("classes:list"), {"q": "Alge"})
    assert b"Algebra" in r.content

    # filter by year (should still show only enrolled that match year)
    r = client.get(reverse("classes:list"), {"year": "4"})
    assert b"Algebra" not in r.content


@pytest.mark.django_db
def test_class_list_for_teacher_shows_own_classes(client):
    teacher = User.objects.create_user("teach", password="pass")
    Group.objects.get_or_create(name="teacher")[0].user_set.add(teacher)
    other = User.objects.create_user("other", password="pass")

    Class.objects.create(name="Chemistry", teacher=teacher, year=2, deadline=timezone.now()+timedelta(days=5))
    Class.objects.create(name="History", teacher=other, year=2, deadline=timezone.now()+timedelta(days=5))

    client.login(username="teach", password="pass")
    r = client.get(reverse("classes:list"))
    assert r.status_code == 200
    content = r.content
    assert b"Chemistry" in content
    assert b"History" not in content


@pytest.mark.django_db
def test_submission_list_filters(client):
    student = User.objects.create_user("s1", password="pass")
    teacher = User.objects.create_user("t1", password="pass")
    Group.objects.get_or_create(name="student")[0].user_set.add(student)
    c1 = Class.objects.create(name="Physics", teacher=teacher, year=5, deadline=timezone.now()+timedelta(days=5))
    c2 = Class.objects.create(name="Maths", teacher=teacher, year=5, deadline=timezone.now()+timedelta(days=5))
    c3 = Class.objects.create(name="Chem", teacher=teacher, year=5, deadline=timezone.now()+timedelta(days=5))
    Enrollment.objects.create(student=student, class_ref=c1)
    Enrollment.objects.create(student=student, class_ref=c2)
    Enrollment.objects.create(student=student, class_ref=c3)

    # Create three submissions for three different classes with different statuses
    from passes.models import Submission
    Submission.objects.create(student=student, class_ref=c1, status="P", file="a.txt")
    Submission.objects.create(student=student, class_ref=c2, status="A", file="b.txt")
    Submission.objects.create(student=student, class_ref=c3, status="R", file="c.txt")

    client.login(username="s1", password="pass")

    # Filter by status
    r = client.get(reverse("submissions:list"), {"status": "A"})
    assert r.status_code == 200
    html = r.content.decode()
    assert "Approved" in html

    # Filter by q (class name)
    r = client.get(reverse("submissions:list"), {"q": "Phys"})
    assert r.status_code == 200


@pytest.mark.django_db
def test_propose_class_access_control(client):
    student = User.objects.create_user("s2", password="pass")
    Group.objects.get_or_create(name="student")[0].user_set.add(student)
    client.login(username="s2", password="pass")
    r = client.get(reverse("classes:propose"))
    assert r.status_code in (302, 403)


@pytest.mark.django_db
def test_proposed_class_form_validation():
    from django.utils import timezone
    from datetime import timedelta
    
    future_date = timezone.now() + timedelta(days=7)
    past_date = timezone.now() - timedelta(days=1)
    
    # Empty name invalid
    form = ProposedClassForm(data={"name": " ", "year": 3, "deadline": future_date})
    assert not form.is_valid()
    assert "name" in form.errors

    # Invalid year
    form = ProposedClassForm(data={"name": "Data", "year": 20, "deadline": future_date})
    assert not form.is_valid()
    assert "year" in form.errors

    # Past deadline invalid
    form = ProposedClassForm(data={"name": "Data", "year": 3, "deadline": past_date})
    assert not form.is_valid()
    assert "deadline" in form.errors

    # Valid
    form = ProposedClassForm(data={
        "name": "Data Structures",
        "year": 3,
        "deadline": future_date,
        "description": "Learn about arrays, linked lists, and trees"
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_class_roster_teacher_view(client):
    """Teachers can see roster with submission status"""
    teacher = User.objects.create_user("teacher", password="pass")
    Group.objects.get_or_create(name="teacher")[0].user_set.add(teacher)
    
    student1 = User.objects.create_user("student1", password="pass", email="s1@test.com")
    student2 = User.objects.create_user("student2", password="pass", email="s2@test.com")
    student3 = User.objects.create_user("student3", password="pass", email="s3@test.com")
    
    cls = Class.objects.create(
        name="Python 101",
        teacher=teacher,
        year=1,
        deadline=timezone.now() + timedelta(days=7)
    )
    
    # Enroll students
    Enrollment.objects.create(student=student1, class_ref=cls)
    Enrollment.objects.create(student=student2, class_ref=cls)
    Enrollment.objects.create(student=student3, class_ref=cls)
    
    # Create submissions with different statuses
    from passes.models import Submission
    Submission.objects.create(student=student1, class_ref=cls, status="A", file="sub1.txt")
    Submission.objects.create(student=student2, class_ref=cls, status="P", file="sub2.txt")
    # student3 has not submitted
    
    client.login(username="teacher", password="pass")
    r = client.get(reverse("classes:roster", args=[cls.id]))
    
    assert r.status_code == 200
    content = r.content.decode()
    
    # Check statistics are shown
    assert "3" in content  # total students
    assert "1" in content  # approved
    assert "1" in content  # pending
    assert "1" in content  # not submitted
    
    # Check student names appear
    assert "student1" in content
    assert "student2" in content
    assert "student3" in content
    
    # Check status badges
    assert "Approved" in content
    assert "Pending" in content
    assert "Not Submitted" in content


@pytest.mark.django_db
def test_class_roster_student_view(client):
    """Students can see roster and have submission form"""
    teacher = User.objects.create_user("teacher", password="pass")
    student1 = User.objects.create_user("student1", password="pass")
    student2 = User.objects.create_user("student2", password="pass")
    
    # Add students to student group
    student_group = Group.objects.create(name="student")
    student1.groups.add(student_group)
    student2.groups.add(student_group)
    
    cls = Class.objects.create(
        name="Java 101",
        teacher=teacher,
        year=2,
        deadline=timezone.now() + timedelta(days=7),
        description="Complete all Java assignments and pass the final exam."
    )
    
    Enrollment.objects.create(student=student1, class_ref=cls)
    Enrollment.objects.create(student=student2, class_ref=cls)
    
    client.login(username="student1", password="pass")
    r = client.get(reverse("classes:roster", args=[cls.id]))
    
    assert r.status_code == 200
    content = r.content.decode()
    
    # Check can see classmates
    assert "student1" in content or "You" in content  # might show as "You"
    assert "student2" in content
    
    # Should see class description
    assert "Complete all Java assignments" in content
    
    # Should see submission form
    assert "Upload File" in content
    assert "Submit Assignment" in content or "Resubmit Assignment" in content
    
    # Should NOT see statistics or status columns (teacher-only)
    assert "Total Students" not in content


@pytest.mark.django_db
def test_class_roster_access_control(client):
    """Only teacher, enrolled students, or staff can access roster"""
    teacher = User.objects.create_user("teacher", password="pass")
    enrolled = User.objects.create_user("enrolled", password="pass")
    outsider = User.objects.create_user("outsider", password="pass")
    
    cls = Class.objects.create(
        name="Access Test",
        teacher=teacher,
        year=1,
        deadline=timezone.now() + timedelta(days=7)
    )
    
    Enrollment.objects.create(student=enrolled, class_ref=cls)
    
    # Outsider should not have access
    client.login(username="outsider", password="pass")
    r = client.get(reverse("classes:roster", args=[cls.id]))
    assert r.status_code == 403
    
    # Enrolled student should have access
    client.login(username="enrolled", password="pass")
    r = client.get(reverse("classes:roster", args=[cls.id]))
    assert r.status_code == 200
    
    # Teacher should have access
    client.login(username="teacher", password="pass")
    r = client.get(reverse("classes:roster", args=[cls.id]))
    assert r.status_code == 200


@pytest.mark.django_db
def test_teacher_cannot_submit_assignments(client):
    """Teachers should not be able to submit assignments"""
    teacher = User.objects.create_user("teacher", password="pass")
    teacher_group = Group.objects.create(name="teacher")
    teacher.groups.add(teacher_group)
    
    student = User.objects.create_user("student", password="pass")
    
    cls = Class.objects.create(
        name="Test Class",
        teacher=teacher,
        year=1,
        deadline=timezone.now() + timedelta(days=7)
    )
    
    Enrollment.objects.create(student=student, class_ref=cls)
    
    # Teacher tries to submit
    client.login(username="teacher", password="pass")
    r = client.post(reverse("submissions:new"), {
        "class_ref": cls.id,
        "file": "test.txt",
    })
    
    # Should be forbidden
    assert r.status_code == 403
    assert "Teachers cannot submit" in r.content.decode()


