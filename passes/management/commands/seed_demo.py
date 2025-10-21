# passes/management/commands/seed_demo.py
from django.core.management.base import BaseCommand
from django_seed import Seed
from django.contrib.auth import get_user_model
from passes.models import Class, Enrollment, Submission
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data using django-seed"

    def handle(self, *args, **options):
        seeder = Seed.seeder(locale="en_US")

        # Create teachers
        seeder.add_entity(User, 3, {
            "is_staff": False,
            "is_superuser": False,
        })

        # Create classes
        seeder.add_entity(Class, 5, {
            "deadline": lambda x: timezone.now() + timedelta(days=random.randint(3, 14)),
            "year": lambda x: random.choice([1, 2, 3]),
            "teacher": lambda x: random.choice(User.objects.all()),
        })

        # Create students
        seeder.add_entity(User, 15, {
            "is_staff": False,
            "is_superuser": False,
        })

        inserted_pks = seeder.execute()

        teachers = User.objects.filter(id__in=inserted_pks[User][:3])
        students = User.objects.filter(id__in=inserted_pks[User][3:])
        classes = Class.objects.filter(id__in=inserted_pks[Class])

        # Enroll students
        for student in students:
            for cls in random.sample(list(classes), k=random.randint(1, len(classes))):
                Enrollment.objects.get_or_create(student=student, class_ref=cls)

        # Create submissions
        for cls in classes:
            for enrollment in cls.enrollments.all():
                Submission.objects.create(
                    student=enrollment.student,
                    class_ref=cls,
                    status=random.choice(["P", "A", "R"]),
                )

        self.stdout.write(self.style.SUCCESS("Seeded demo data successfully!"))
