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
    # Empty name invalid
    form = ProposedClassForm(data={"name": " ", "year": 3})
    assert not form.is_valid()
    assert "name" in form.errors

    # Invalid year
    form = ProposedClassForm(data={"name": "Data", "year": 20})
    assert not form.is_valid()
    assert "year" in form.errors

    # Valid
    form = ProposedClassForm(data={"name": "Data", "year": 3})
    assert form.is_valid()
