from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from passes.models import TeacherApplication


class Command(BaseCommand):
    help = "Activate users with approved TeacherApplication and add to teacher group"

    def handle(self, *args, **options):
        teacher_group, _ = Group.objects.get_or_create(name="teacher")
        fixed = 0
        for app in TeacherApplication.objects.filter(status="A"):
            user = app.user
            if user:
                user.groups.add(teacher_group)
                if not user.is_active:
                    user.is_active = True
                    user.save(update_fields=["is_active"])
                    fixed += 1
        self.stdout.write(self.style.SUCCESS(f"Ensured activation for {fixed} approved teacher(s)."))
