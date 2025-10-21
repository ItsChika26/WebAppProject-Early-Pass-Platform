from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from datetime import timedelta
from django.conf import settings

User = get_user_model()


class Profile(models.Model):
    """
    Per-user profile to store student year (and future attributes).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    student_year = models.PositiveIntegerField(null=True, blank=True, help_text="Student's year group if applicable")

    def __str__(self):
        return f"Profile({self.user})"


class Class(models.Model):
    """
    A course/class taught by exactly one teacher.
    Students in the same year will typically share the same classes.
    """
    name = models.CharField(max_length=120)
    teacher = models.ForeignKey(User, on_delete=models.PROTECT, related_name="classes_taught")
    year = models.PositiveIntegerField(help_text="Year group, e.g., 1, 2, 3")
    deadline = models.DateTimeField()

    class Meta:
        ordering = ["deadline", "name"]
        verbose_name_plural = "Classes"
        constraints = [
            # Optional: avoid duplicate class names for the same year/teacher
            models.UniqueConstraint(fields=["name", "year", "teacher"], name="uq_class_name_year_teacher")
        ]

    def __str__(self):
        return f"{self.name} (Y{self.year})"

    @property
    def is_past_deadline(self) -> bool:
        return timezone.now() > self.deadline


class Enrollment(models.Model):
    """
    Many-to-many between Students and Classes with an explicit model.
    Keeping it explicit lets you later add fields (e.g., joined_at).
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    class_ref = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="enrollments")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("student", "class_ref")]
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.student} ↔ {self.class_ref}"


class TeacherApplication(models.Model):
    """
    A teacher self-declares during signup. Admin must approve.
    We capture the intended course names and target years.
    """
    STATUS = [
        ("P", "Pending"),
        ("A", "Approved"),
        ("R", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="teacher_applications")
    is_teacher = models.BooleanField(default=False)
    course_names = models.JSONField(default=list, help_text="List of course names the teacher plans to teach")
    years = models.JSONField(default=list, help_text="List of year integers, e.g., [1,2,3]")
    status = models.CharField(max_length=1, choices=STATUS, default="P")
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"TeacherApplication({self.user}, status={self.get_status_display()})"

    @transaction.atomic
    def approve(self, default_deadline_days: int | None = None) -> list['Class']:
        """
        Approve this application: mark approved, add user to 'teacher' group,
        create Class rows for each (course_name, year), and auto-enroll students
        in the same year to these classes.
        Returns the list of created Class instances.
        """
        if self.status == "A":
            return list(Class.objects.filter(teacher=self.user, name__in=self.course_names, year__in=self.years))

        self.status = "A"
        self.decided_at = timezone.now()
        self.save(update_fields=["status", "decided_at"])

        # Ensure teacher group exists and add user
        teacher_group, _ = Group.objects.get_or_create(name="teacher")
        self.user.groups.add(teacher_group)
        # Allow login now
        if not self.user.is_active:
            self.user.is_active = True
            self.user.save(update_fields=["is_active"])

        # Create classes (avoid duplicates thanks to unique constraint)
        created_classes = []
        days = (
            default_deadline_days
            if default_deadline_days is not None
            else getattr(settings, "DEFAULT_CLASS_DEADLINE_DAYS", 30)
        )
        deadline = timezone.now() + timedelta(days=days)
        for cname in self.course_names:
            cname = (cname or "").strip()
            if not cname:
                continue
            for y in self.years:
                try:
                    cls, _ = Class.objects.get_or_create(
                        name=cname,
                        year=int(y),
                        teacher=self.user,
                        defaults={"deadline": deadline},
                    )
                    created_classes.append(cls)
                except Exception:
                    # In case of race/constraint issues, skip to next
                    continue

        # Auto-enroll users by matching profile.student_year
        # Build dict year -> classes
        by_year = {}
        for cls in created_classes:
            by_year.setdefault(cls.year, []).append(cls)

        for year, classes in by_year.items():
            students = User.objects.filter(profile__student_year=year).distinct()
            # Create enrollments idempotently
            for student in students:
                for cls in classes:
                    Enrollment.objects.get_or_create(student=student, class_ref=cls)

        return created_classes


class ProposedClass(models.Model):
    """
    Teachers can propose additional classes post-registration. Requires admin approval.
    """
    STATUS = [
        ("P", "Pending"),
        ("A", "Approved"),
        ("R", "Rejected"),
    ]

    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="proposed_classes")
    name = models.CharField(max_length=120)
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=1, choices=STATUS, default="P")
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["teacher", "name", "year", "status"], name="uq_proposedclass_teacher_name_year_status")
        ]

    def __str__(self):
        return f"ProposedClass({self.name}, Y{self.year}, {self.get_status_display()})"

    @transaction.atomic
    def approve(self, default_deadline_days: int | None = None) -> 'Class':
        # Ensure a Class exists and students are enrolled; if status isn't approved, mark approved
        if self.status != "A":
            self.status = "A"
            self.decided_at = timezone.now()
            self.save(update_fields=["status", "decided_at"])

        # Create or fetch the class
        days = (
            default_deadline_days
            if default_deadline_days is not None
            else getattr(settings, "DEFAULT_CLASS_DEADLINE_DAYS", 30)
        )
        deadline = timezone.now() + timedelta(days=days)
        cls, _ = Class.objects.get_or_create(
            name=self.name,
            year=self.year,
            teacher=self.teacher,
            defaults={"deadline": deadline},
        )
        # Auto-enroll matching year students
        students = User.objects.filter(profile__student_year=self.year)
        for s in students:
            Enrollment.objects.get_or_create(student=s, class_ref=cls)
        return cls


def submission_upload_to(instance: "Submission", filename: str) -> str:
    """
    Store per-class and per-student for tidy media folders:
    media/submissions/<class_id>/<student_id>/<filename>
    """
    return f"submissions/{instance.class_ref_id}/{instance.student_id}/{filename}"


ALLOWED_EXTS = ["pdf", "doc", "docx", "txt", "zip", "py", "ipynb", "md"]


class Submission(models.Model):
    STATUS = [
        ("P", "Pending"),
        ("A", "Approved"),
        ("R", "Rejected"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    class_ref = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="submissions")
    file = models.FileField(
        upload_to=submission_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTS)],
        help_text=f"Allowed: {', '.join(ALLOWED_EXTS)}",
    )
    status = models.CharField(max_length=1, choices=STATUS, default="P")
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            # A student should submit at most once per class (you can relax later if you want versions)
            models.UniqueConstraint(fields=["student", "class_ref"], name="uq_student_class_single_submission")
        ]

    def __str__(self):
        return f"{self.student} → {self.class_ref} [{self.get_status_display()}]"

    # passes/models.py
    def clean(self):
        if not self.student_id or not self.class_ref_id:
            return
        if not Enrollment.objects.filter(student_id=self.student_id, class_ref_id=self.class_ref_id).exists():
            raise ValidationError("You are not enrolled in this class.")
        if timezone.now() > self.class_ref.deadline and self.status == "P":
            raise ValidationError("Deadline has passed for this class.")
