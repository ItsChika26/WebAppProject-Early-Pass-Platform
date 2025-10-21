import pytest
from django.contrib.auth.models import User, Group
from django.urls import reverse

from passes.models import TeacherApplication, ProposedClass, Class
from passes.models import Profile, Enrollment
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
def test_teacher_application_signal_activates_and_groups_user():
    u = User.objects.create_user("t2", password="pass", is_active=False)
    assert not u.is_active
    # Ensure teacher group does not exist yet
    Group.objects.filter(name="teacher").delete()

    # Creating approved application should trigger activation and group add
    TeacherApplication.objects.create(
        user=u,
        is_teacher=True,
        course_names=["X"],
        years=[1],
        status="A",
    )
    u.refresh_from_db()
    assert u.is_active
    assert u.groups.filter(name="teacher").exists()


@pytest.mark.django_db
def test_proposed_class_signal_creates_class_on_status_change():
    teacher = User.objects.create_user("teachsig", password="pass")
    # Start pending
    pc = ProposedClass.objects.create(teacher=teacher, name="Signal Test", year=9, status="P")
    # Approve via status change (simulating admin save)
    pc.status = "A"
    pc.save()
    assert Class.objects.filter(name="Signal Test", year=9, teacher=teacher).exists()


@pytest.mark.django_db
def test_navbar_logout_post_shows_when_authenticated(client):
    u = User.objects.create_user("hasnav", password="pass")
    client.login(username="hasnav", password="pass")
    r = client.get(reverse("home"))
    assert r.status_code == 200
    # Should render a POST form to /accounts/logout/ (not a GET link)
    html = r.content.decode()
    assert "/accounts/logout/" in html
    assert "method=\"post\"" in html.lower() or "method='post'" in html.lower()


@pytest.mark.django_db
def test_submission_reject_htmx(client):
    # Setup user, class, enrollment, submission
    teacher = User.objects.create_user("teachrej", password="pass")
    Group.objects.get_or_create(name="teacher")[0].user_set.add(teacher)
    cls = Class.objects.create(name="RejCls", teacher=teacher, year=1, deadline="2099-01-01T00:00:00Z")

    from passes.models import Submission, Enrollment
    student = User.objects.create_user("studrej", password="pass")
    Enrollment.objects.create(student=student, class_ref=cls)
    sub = Submission.objects.create(student=student, class_ref=cls, status="P", file="dummy.txt")

    client.login(username="teachrej", password="pass")
    r = client.post(reverse("submissions:reject", args=[sub.id]), HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    sub.refresh_from_db()
    assert sub.status == "R"


@pytest.mark.django_db
def test_profile_auto_enrolls_into_existing_classes():
    teacher = User.objects.create_user("teachauto", password="pass")
    c1 = Class.objects.create(name="Auto 1", teacher=teacher, year=3, deadline=timezone.now()+timedelta(days=10))
    c2 = Class.objects.create(name="Auto 2", teacher=teacher, year=3, deadline=timezone.now()+timedelta(days=10))

    student = User.objects.create_user("studauto", password="pass")
    # Creating profile with year should trigger auto enrollment via signal
    Profile.objects.create(user=student, student_year=3)

    assert Enrollment.objects.filter(student=student, class_ref=c1).exists()
    assert Enrollment.objects.filter(student=student, class_ref=c2).exists()
