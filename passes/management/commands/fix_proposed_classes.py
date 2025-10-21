from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
from passes.models import ProposedClass, Class, Enrollment


class Command(BaseCommand):
    help = "Ensure approved ProposedClass items have real Class records and enrolled students."

    def add_arguments(self, parser):
        parser.add_argument("--deadline-days", type=int, default=30, help="Default deadline offset in days")

    def handle(self, *args, **options):
        User = get_user_model()
        count_classes = 0
        count_enrolls = 0
        deadline = timezone.now() + timedelta(days=options["deadline_days"])
        approved = ProposedClass.objects.filter(status="A")
        for pc in approved:
            cls, created = Class.objects.get_or_create(
                name=pc.name,
                year=pc.year,
                teacher=pc.teacher,
                defaults={"deadline": deadline},
            )
            if created:
                count_classes += 1
            # Enroll same-year students
            students = User.objects.filter(profile__student_year=pc.year)
            for s in students:
                _, en_created = Enrollment.objects.get_or_create(student=s, class_ref=cls)
                if en_created:
                    count_enrolls += 1

        self.stdout.write(self.style.SUCCESS(
            f"Ensured {approved.count()} approved proposals; created {count_classes} classes and {count_enrolls} enrollments."
        ))
