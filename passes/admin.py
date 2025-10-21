from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Class, Enrollment, Submission, TeacherApplication, Profile, ProposedClass


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher", "year", "deadline")
    list_filter = ("year", "teacher")
    search_fields = ("name", "teacher__username", "teacher__first_name", "teacher__last_name")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "class_ref", "joined_at")
    list_filter = ("class_ref__year",)
    search_fields = ("student__username", "class_ref__name")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("student", "class_ref", "status", "submitted_at")
    list_filter = ("status", "class_ref__year")
    search_fields = ("student__username", "class_ref__name", "feedback")
    readonly_fields = ("submitted_at", "updated_at")


@admin.register(TeacherApplication)
class TeacherApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "is_teacher", "status", "created_at", "decided_at")
    list_filter = ("status", "is_teacher")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "decided_at", "course_names", "years")

    actions = ["approve_applications", "reject_applications"]

    def approve_applications(self, request, queryset):
        count_apps = 0
        for app in queryset.filter(status="P"):
            app.approve()
            count_apps += 1
        # For already approved ones, ensure activation too via signal
        for app in queryset.filter(status="A"):
            app.save(update_fields=["status"])  # trigger post_save to enforce activation
        self.message_user(
            request, 
            _(f"Approved {count_apps} applications. Teachers can now log in and propose classes."), 
            level=messages.SUCCESS
        )

    approve_applications.short_description = _("Approve selected teacher applications")

    def reject_applications(self, request, queryset):
        updated = queryset.filter(status="P").update(status="R")
        self.message_user(request, _(f"Rejected {updated} applications."), level=messages.WARNING)

    reject_applications.short_description = _("Reject selected applications")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "student_year")
    list_filter = ("student_year",)
    search_fields = ("user__username", "user__email")


@admin.register(ProposedClass)
class ProposedClassAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher", "year", "deadline", "status", "created_at")
    list_filter = ("status", "year")
    search_fields = ("name", "teacher__username", "description")
    readonly_fields = ("created_at", "decided_at")
    actions = ["approve_proposals", "reject_proposals"]

    def approve_proposals(self, request, queryset):
        count = 0
        # Approve both pending and already-approved to ensure classes exist
        for pc in queryset.filter(status__in=["P", "A"]):
            pc.approve()
            count += 1
        self.message_user(request, _(f"Processed {count} proposed classes (created/ensured classes and enrollments)."), level=messages.SUCCESS)

    def reject_proposals(self, request, queryset):
        updated = queryset.filter(status="P").update(status="R")
        self.message_user(request, _(f"Rejected {updated} proposed classes."), level=messages.WARNING)
