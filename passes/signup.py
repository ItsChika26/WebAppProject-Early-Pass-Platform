from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Profile, TeacherApplication
from django.contrib.auth.models import Group


class ExtendedSignupForm(SignupForm):
    is_teacher = forms.BooleanField(
        required=False, 
        label=_("I am a teacher"),
        help_text=_("Check this box if you're applying as a teacher. You'll be able to propose classes after approval.")
    )
    student_year = forms.IntegerField(
        required=False,
        min_value=1,
        label=_("Your year (if student)"),
        help_text=_("Provide your year if you're a student for auto-enrollment."),
    )

    def save(self, request):
        user = super().save(request)

        # Ensure a Profile exists and capture student year
        student_year = self.cleaned_data.get("student_year")
        Profile.objects.update_or_create(user=user, defaults={"student_year": student_year})

        # If teacher, create a pending TeacherApplication
        if self.cleaned_data.get("is_teacher"):
            TeacherApplication.objects.create(
                user=user,
                is_teacher=True,
                course_names=[],  # Empty initially - teacher will propose classes after approval
                years=[],  # Empty initially
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
