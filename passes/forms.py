from django import forms
from .models import Submission, ProposedClass

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["class_ref", "file", "feedback"]
        widgets = {
            "class_ref": forms.Select(attrs={"class": "form-select"}),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "feedback": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Optional note to teacher"})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        # Limit class choices to *enrolled* classes for this student
        if user is not None:
            self.fields["class_ref"].queryset = (
                user.enrollments.select_related("class_ref")
                .values_list("class_ref", flat=True)
            )
            # Re-query to actual Class objects (clean way without an extra query loop)
            from .models import Class as Course  # local import to avoid circular
            self.fields["class_ref"].queryset = Course.objects.filter(
                id__in=user.enrollments.values_list("class_ref_id", flat=True)
            )


class ProposedClassForm(forms.ModelForm):
    class Meta:
        model = ProposedClass
        fields = ["name", "year", "deadline", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Introduction to Python"}),
            "year": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 12}),
            "deadline": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                    "placeholder": "Describe what students need to do to pass this class (e.g., assignments, projects, exams)"
                }
            )
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Class name is required.")
        return name

    def clean_year(self):
        year = self.cleaned_data.get("year")
        if year is None:
            raise forms.ValidationError("Year is required.")
        if not (1 <= int(year) <= 12):
            raise forms.ValidationError("Year must be between 1 and 12.")
        return year
    
    def clean_deadline(self):
        from django.utils import timezone
        deadline = self.cleaned_data.get("deadline")
        if deadline and deadline <= timezone.now():
            raise forms.ValidationError("Deadline must be in the future.")
        return deadline
