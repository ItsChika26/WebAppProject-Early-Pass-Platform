from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Profile, TeacherApplication
from django.contrib.auth.models import Group


class ExtendedSignupForm(SignupForm):
    is_teacher = forms.BooleanField(required=False, label=_("I am a teacher"))
    teacher_courses = forms.CharField(
        required=False,
        label=_("Courses you teach"),
        help_text=_("Comma-separated list, e.g., Intro to DB, Algorithms I"),
    )
    teacher_years = forms.CharField(
        required=False,
        label=_("Years you teach"),
        help_text=_("Comma-separated years, e.g., 1, 2, 3"),
    )
    student_year = forms.IntegerField(
        required=False,
        min_value=1,
        label=_("Your year (if student)"),
        help_text=_("Provide your year if you're a student for auto-enrollment."),
    )

    def clean(self):
        cleaned = super().clean()
        is_teacher = cleaned.get("is_teacher")
        if is_teacher:
            if not cleaned.get("teacher_courses"):
                self.add_error("teacher_courses", _("Please list the courses you teach."))
            if not cleaned.get("teacher_years"):
                self.add_error("teacher_years", _("Please list the years you teach."))
            # parse and validate here to surface errors early
            courses_raw = cleaned.get("teacher_courses", "") or ""
            years_raw = cleaned.get("teacher_years", "") or ""
            course_names = [c.strip() for c in courses_raw.split(",") if c.strip()]
            if not course_names:
                self.add_error("teacher_courses", _("Please provide at least one course."))
            # Validate years are integers in range 1..12
            years = []
            year_errors = []
            for part in years_raw.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    y = int(part)
                    if 1 <= y <= 12:
                        years.append(y)
                    else:
                        year_errors.append(part)
                except ValueError:
                    year_errors.append(part)
            if not years:
                self.add_error("teacher_years", _("Please enter valid years between 1 and 12."))
            elif year_errors:
                self.add_error("teacher_years", _("Invalid year values: ") + ", ".join(year_errors))
        return cleaned

    def save(self, request):
        user = super().save(request)

        # Ensure a Profile exists and capture student year
        student_year = self.cleaned_data.get("student_year")
        Profile.objects.update_or_create(user=user, defaults={"student_year": student_year})

        # If teacher, create a pending TeacherApplication
        if self.cleaned_data.get("is_teacher"):
            courses_raw = self.cleaned_data.get("teacher_courses", "") or ""
            years_raw = self.cleaned_data.get("teacher_years", "") or ""
            course_names = [c.strip() for c in courses_raw.split(",") if c.strip()]
            years = []
            for part in years_raw.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    years.append(int(part))
                except ValueError:
                    continue
            TeacherApplication.objects.create(
                user=user,
                is_teacher=True,
                course_names=course_names,
                years=years,
                status="P",
            )
            # Teacher accounts are inactive until first approval
            user.is_active = False
            user.save(update_fields=["is_active"])
        else:
            # Not a teacher; if student_year provided, add to 'student' group
            if student_year:
                student_group, _ = Group.objects.get_or_create(name="student")
                user.groups.add(student_group)
        return user
