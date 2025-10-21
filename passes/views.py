# passes/views.py
from django import forms
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
            "is_teacher": is_teacher,
        },
    )


@login_required
def submission_create(request):
    # Prevent teachers from submitting - only students can submit
    if request.user.groups.filter(name="teacher").exists():
        return HttpResponseForbidden("Teachers cannot submit assignments. Only students can submit.")
    
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
            # If coming from roster page, redirect back there
            if 'from_roster' in request.POST or request.META.get('HTTP_REFERER', '').endswith(f'/classes/{class_ref.id}/roster/'):
                return redirect('classes:roster', class_id=class_ref.id)
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


@login_required
def class_roster(request, class_id):
    """
    Show the list of students enrolled in a class.
    Teachers can see submission status for each student.
    Students can see their classmates and submit assignments.
    """
    cls = get_object_or_404(Class, id=class_id)
    user = request.user
    
    # Check permissions: must be the teacher, enrolled student, or staff
    is_teacher = cls.teacher == user or user.is_staff
    is_enrolled = Enrollment.objects.filter(student=user, class_ref=cls).exists()
    
    if not (is_teacher or is_enrolled):
        return HttpResponseForbidden("You don't have access to this class roster.")
    
    # Get all enrollments with related student data
    enrollments = cls.enrollments.select_related('student').order_by('student__username')
    
    # For teachers, annotate each enrollment with submission status
    roster_data = []
    for enrollment in enrollments:
        student_data = {
            'enrollment': enrollment,
            'student': enrollment.student,
        }
        
        if is_teacher:
            # Check if student has submitted
            try:
                submission = Submission.objects.get(
                    student=enrollment.student,
                    class_ref=cls
                )
                student_data['submission'] = submission
                student_data['status'] = submission.get_status_display()
                student_data['status_code'] = submission.status
            except Submission.DoesNotExist:
                student_data['submission'] = None
                student_data['status'] = 'Not Submitted'
                student_data['status_code'] = 'N'
        
        roster_data.append(student_data)
    
    context = {
        'class': cls,
        'roster_data': roster_data,
        'is_teacher': is_teacher,
        'total_students': len(roster_data),
    }
    
    if is_teacher:
        # Calculate statistics for teacher view
        submitted = sum(1 for d in roster_data if d.get('submission'))
        approved = sum(1 for d in roster_data if d.get('status_code') == 'A')
        rejected = sum(1 for d in roster_data if d.get('status_code') == 'R')
        pending = sum(1 for d in roster_data if d.get('status_code') == 'P')
        not_submitted = sum(1 for d in roster_data if d.get('status_code') == 'N')
        
        context.update({
            'stats': {
                'submitted': submitted,
                'approved': approved,
                'rejected': rejected,
                'pending': pending,
                'not_submitted': not_submitted,
            }
        })
    else:
        # For students: check their submission status and provide a form
        try:
            user_submission = Submission.objects.get(student=user, class_ref=cls)
            context['user_submission'] = user_submission
        except Submission.DoesNotExist:
            context['user_submission'] = None
        
        # Create a submission form pre-filled with the current class
        form = SubmissionForm(user=user, initial={'class_ref': cls})
        # Make class_ref hidden since we're already on this class page
        form.fields['class_ref'].widget = forms.HiddenInput()
        context['submission_form'] = form
    
    return render(request, "passes/class_roster.html", context)


