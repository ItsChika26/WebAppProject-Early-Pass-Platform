from django.conf import settings
from django.core.mail import mail_admins
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TeacherApplication, ProposedClass, Profile
from django.contrib.auth.models import Group


@receiver(post_save, sender=TeacherApplication)
def notify_admins_on_teacher_application(sender, instance: TeacherApplication, created: bool, **kwargs):
    # Only notify when first created and pending and flagged as teacher
    if not created:
        return
    if not instance.is_teacher:
        return
    if instance.status != "P":
        return

    if not getattr(settings, "ADMINS", None):
        # No admins configured; nothing to notify
        return

    subject = "New teacher application submitted"
    lines = [
        f"User: {instance.user} (id={instance.user_id})",
        f"Courses: {', '.join(instance.course_names) or '(none)'}",
        f"Years: {', '.join(str(y) for y in instance.years) or '(none)'}",
        "",
        "Review pending applications:",
        "/admin/passes/teacherapplication/",
    ]
    body = "\n".join(lines)
    mail_admins(subject, body, fail_silently=True)


@receiver(post_save, sender=TeacherApplication)
def activate_user_on_teacher_approval(sender, instance: TeacherApplication, created: bool, **kwargs):
    # If an application is saved as approved, ensure the user is activated and added to teacher group
    if instance.status == "A" and instance.user:
        teacher_group, _ = Group.objects.get_or_create(name="teacher")
        instance.user.groups.add(teacher_group)
        if not instance.user.is_active:
            instance.user.is_active = True
            instance.user.save(update_fields=["is_active"])


@receiver(post_save, sender=ProposedClass)
def ensure_class_on_proposed_approval(sender, instance: ProposedClass, created: bool, **kwargs):
    # If a proposed class is saved as approved (e.g., via admin change page), ensure Class and enrollments exist
    if instance.status == "A":
        instance.approve()


@receiver(post_save, sender=Profile)
def auto_enroll_student_on_profile_year(sender, instance: Profile, created: bool, **kwargs):
    """
    When a Profile with a student_year is created or updated, automatically
    enroll the user into all existing classes for that year. Idempotent.
    """
    year = instance.student_year
    if not year:
        return
    try:
        from .models import Class, Enrollment
        classes = Class.objects.filter(year=year)
        for cls in classes:
            Enrollment.objects.get_or_create(student=instance.user, class_ref=cls)
    except Exception:
        # Avoid hard failures in signals; log if needed in production
        pass
