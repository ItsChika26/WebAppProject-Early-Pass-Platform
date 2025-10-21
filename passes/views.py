# passes/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import Class, Submission, Enrollment
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import SubmissionForm, ProposedClassForm


@ensure_csrf_cookie
def home(request):
    return render(request, "home.html")


@login_required
def class_list(request):
    """
    Students: show enrolled classes.
    Teachers: show classes they teach.
    Admin/staff: show all classes.
    """
    user = request.user
    if user.is_staff:
        qs = Class.objects.all()
    elif user.groups.filter(name="teacher").exists():
        qs = Class.objects.filter(teacher=user)
    else:
        qs = Class.objects.filter(enrollments__student=user)
    q = request.GET.get("q", "")
    year = request.GET.get("year")
    if q:
        qs = qs.filter(name__icontains=q)
    if year:
        qs = qs.filter(year=year)

    template = "passes/partials/class_table.html" if request.htmx else "passes/class_list.html"
    is_teacher = request.user.groups.filter(name="teacher").exists()
    show_propose_button = request.user.is_authenticated and (request.user.is_staff or is_teacher)
    # Build dynamic year options
    years = (
        Class.objects.order_by().values_list("year", flat=True).distinct().order_by("year")
    )
    return render(
        request,
        template,
        {
            "classes": qs.order_by("deadline").distinct(),
            "is_teacher": is_teacher,
            "show_propose_button": show_propose_button,
            "years": years,
        },
    )


@login_required
def submission_list(request):
    """
    Students: their own submissions.
    Teachers: submissions to their classes.
    Staff: all submissions.
    """
    user = request.user
    is_teacher = user.groups.filter(name="teacher").exists()
    if user.is_staff:
        qs = Submission.objects.select_related("class_ref", "student")
        class_options = Class.objects.all()
    elif is_teacher:
        qs = Submission.objects.select_related("class_ref", "student").filter(class_ref__teacher=user)
        class_options = Class.objects.filter(teacher=user)
    else:
        qs = Submission.objects.select_related("class_ref", "student").filter(student=user)
        class_options = Class.objects.filter(enrollments__student=user).distinct()

    # Filters
    status = request.GET.get("status", "")
    class_id = request.GET.get("class", "")
    q = request.GET.get("q", "")
    if status in {"P", "A", "R"}:
        qs = qs.filter(status=status)
    if class_id and class_id.isdigit():
        qs = qs.filter(class_ref_id=int(class_id))
    if q:
        qs = qs.filter(Q(class_ref__name__icontains=q) | Q(student__username__icontains=q))

    template = "passes/partials/submission_table.html" if request.htmx else "passes/submission_list.html"
    return render(
        request,
        template,
        {
            "submissions": qs,
            "class_options": class_options.order_by("name"),
            "selected_status": status,
            "selected_class": class_id,
            "q": q,
        },
    )


@login_required
def submission_create(request):
    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            class_ref = form.cleaned_data["class_ref"]
            file = form.cleaned_data["file"]
            feedback = form.cleaned_data.get("feedback", "")

            # either create or update the existing submission
            sub, created = Submission.objects.get_or_create(
                student=request.user,
                class_ref=class_ref,
                defaults={"status": "P"},
            )
            # replace/update
            sub.file = file
            sub.feedback = feedback
            sub.status = "P"           # reset review state on resubmission
            sub.save()

            if request.htmx:
                return render(request, "passes/partials/submit_success.html", {"sub": sub})
            return redirect("submissions:list")

        # invalid form
        if request.htmx:
            r = render(request, "passes/partials/submission_form_inner.html", {"form": form})
            r.status_code = 422
            return r

    else:
        form = SubmissionForm(user=request.user)

    return render(request, "passes/submission_form.html", {"form": form})
@require_POST
@login_required
def submission_approve(request, pk: int):
    sub = get_object_or_404(Submission.objects.select_related("class_ref"), pk=pk)
    user = request.user
    if not (user.is_staff or sub.class_ref.teacher_id == user.id):
        return HttpResponseForbidden()
    sub.status = "A"
    sub.save(update_fields=["status", "updated_at"])
    if getattr(request, "htmx", False):
        html = render_to_string("passes/partials/submission_row.html", {"obj": sub}, request=request)
        return HttpResponse(html)
    return redirect("submissions:list")


@require_POST
@login_required
def submission_reject(request, pk: int):
    sub = get_object_or_404(Submission.objects.select_related("class_ref"), pk=pk)
    user = request.user
    if not (user.is_staff or sub.class_ref.teacher_id == user.id):
        return HttpResponseForbidden()
    sub.status = "R"
    sub.save(update_fields=["status", "updated_at"])
    if getattr(request, "htmx", False):
        html = render_to_string("passes/partials/submission_row.html", {"obj": sub}, request=request)
        return HttpResponse(html)
    return redirect("submissions:list")


@login_required
def propose_class(request):
    # Only teachers can propose classes
    if not request.user.groups.filter(name="teacher").exists() and not request.user.is_staff:
        return HttpResponseForbidden()
    if request.method == "POST":
        form = ProposedClassForm(request.POST)
        if form.is_valid():
            pc = form.save(commit=False)
            pc.teacher = request.user
            pc.status = "P"
            pc.save()
            return redirect("classes:list")
    else:
        form = ProposedClassForm()
    return render(request, "passes/propose_class.html", {"form": form})


@login_required
def my_proposals(request):
    if not request.user.groups.filter(name="teacher").exists() and not request.user.is_staff:
        return HttpResponseForbidden()
    qs = request.user.proposed_classes.all().order_by("-created_at")
    return render(request, "passes/my_proposals.html", {"proposals": qs})

