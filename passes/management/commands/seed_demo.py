# passes/management/commands/seed_demo.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from passes.models import Class, Enrollment, Submission, Profile, TeacherApplication
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
import random
import os

User = get_user_model()



class Command(BaseCommand):
    help = "Seed demo data with teachers, students, classes, and submissions"

    # Sample file content templates
    PYTHON_TEMPLATES = [
        '''# Assignment Solution
def calculate_sum(numbers):
    """Calculate the sum of a list of numbers"""
    return sum(numbers)

def main():
    test_data = [1, 2, 3, 4, 5]
    result = calculate_sum(test_data)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
''',
        '''# Data Structures Implementation
class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None
    
    def is_empty(self):
        return len(self.items) == 0

# Test the stack
stack = Stack()
stack.push(1)
stack.push(2)
print(stack.pop())  # Output: 2
''',
        '''# Database Query Example
import sqlite3

def get_students_by_year(year):
    """Fetch all students in a given year"""
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM students WHERE year = ?"
    cursor.execute(query, (year,))
    
    results = cursor.fetchall()
    conn.close()
    return results

# Example usage
students = get_students_by_year(2)
for student in students:
    print(student)
''',
    ]

    TEXT_TEMPLATES = [
        '''Assignment Report

Student Name: {student}
Course: {course}
Date Submitted: {date}

Introduction:
This assignment explores the fundamental concepts of {topic}. Through research 
and practical examples, I have gained a deeper understanding of the subject matter.

Main Content:
The key findings of this assignment demonstrate that {topic} plays a crucial role 
in modern software development. By implementing best practices and following 
established patterns, we can create more maintainable and scalable solutions.

Conclusion:
In conclusion, this assignment has provided valuable insights into {topic}. 
The practical applications of these concepts will be beneficial in future projects.

References:
- Introduction to {topic}, 2024
- Advanced Concepts in Computer Science
- Best Practices Guide
''',
        '''Lab Report - {course}

Objective:
To understand and implement {topic} concepts in a practical setting.

Methodology:
1. Research existing implementations
2. Design the solution architecture
3. Implement the code
4. Test and validate results
5. Document findings

Results:
The implementation successfully demonstrates the core principles of {topic}.
Performance metrics show that the solution meets all specified requirements.

Analysis:
Through this lab, I learned that {topic} requires careful consideration of
multiple factors including efficiency, maintainability, and scalability.

Conclusion:
The lab objectives were successfully achieved. Future improvements could include
optimization and additional feature implementations.
''',
        '''Essay on {topic}

By: {student}
Course: {course}

Abstract:
This essay examines the importance of {topic} in modern computing. Through
analysis and examples, we explore how this concept influences software design.

Part 1: Background
{topic} has been a cornerstone of computer science for decades. Understanding
its principles is essential for any developer working in the field.

Part 2: Applications
In practice, {topic} is used extensively in:
- Web development frameworks
- Database management systems
- Operating system design
- Network protocols

Part 3: Critical Analysis
While {topic} offers many advantages, it also presents challenges that must
be carefully managed. Trade-offs between different approaches should be
considered based on specific project requirements.

Conclusion:
Mastery of {topic} is crucial for building robust and efficient systems.
This essay has explored the theoretical foundations and practical applications.
''',
    ]

    def generate_file_content(self, file_type, student, course):
        """Generate random file content based on type"""
        topics = [
            "algorithms and data structures",
            "database normalization",
            "object-oriented programming",
            "web security principles",
            "software testing methodologies",
            "network architecture",
            "cloud computing",
            "machine learning basics",
        ]
        
        if file_type == "py":
            return random.choice(self.PYTHON_TEMPLATES)
        else:  # txt
            template = random.choice(self.TEXT_TEMPLATES)
            return template.format(
                student=student,
                course=course,
                topic=random.choice(topics),
                date=timezone.now().strftime("%Y-%m-%d")
            )

    def handle(self, *args, **options):
        self.stdout.write("Creating groups...")
        student_group, _ = Group.objects.get_or_create(name="student")
        teacher_group, _ = Group.objects.get_or_create(name="teacher")

        # Create teachers with approved applications
        self.stdout.write("Creating teachers...")
        teachers = []
        teacher_names = ["Prof. Smith", "Dr. Johnson", "Ms. Williams"]
        for i, name in enumerate(teacher_names, 1):
            username = f"teacher{i}"
            if User.objects.filter(username=username).exists():
                teacher = User.objects.get(username=username)
            else:
                teacher = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password="teacher123",
                    first_name=name.split()[-1],
                    is_active=True
                )
            teacher.groups.add(teacher_group)
            Profile.objects.get_or_create(user=teacher)
            teachers.append(teacher)

        # Create approved teacher applications for context
        self.stdout.write("Creating teacher applications...")
        for teacher in teachers:
            if not TeacherApplication.objects.filter(user=teacher, status="A").exists():
                TeacherApplication.objects.create(
                    user=teacher,
                    is_teacher=True,
                    course_names=[],  # Empty - teachers propose classes instead
                    years=[],
                    status="A",
                    decided_at=timezone.now()
                )

        # Create classes
        self.stdout.write("Creating classes...")
        classes = []
        course_data = [
            {
                "name": "Web Development",
                "description": "Complete all HTML, CSS, and JavaScript projects. Submit a final portfolio website demonstrating responsive design and modern web standards."
            },
            {
                "name": "Database Systems",
                "description": "Master SQL queries and database design. Final project requires creating a normalized database schema with at least 5 tables and complex queries."
            },
            {
                "name": "Algorithms",
                "description": "Solve algorithm challenges weekly. Pass requires implementing sorting algorithms, graph traversal, and dynamic programming solutions with optimal time complexity."
            },
            {
                "name": "Data Structures",
                "description": "Implement core data structures from scratch: linked lists, trees, hash tables, and graphs. Submit working code with comprehensive test cases."
            },
            {
                "name": "Software Engineering",
                "description": "Complete team project using Agile methodology. Requirements include version control, unit tests, documentation, and a working deployed application."
            },
            {
                "name": "Operating Systems",
                "description": "Complete all lab assignments on process management, memory allocation, and file systems. Final exam covers scheduling algorithms and deadlock prevention."
            },
            {
                "name": "Computer Networks",
                "description": "Understand network protocols and architecture. Submit packet analysis reports and implement a simple client-server application using sockets."
            },
            {
                "name": "Machine Learning",
                "description": "Complete hands-on projects with supervised and unsupervised learning. Final project requires training a model on real-world data with 85%+ accuracy."
            }
        ]
        
        for i, course_info in enumerate(course_data):
            teacher = teachers[i % len(teachers)]
            year = (i % 3) + 1  # Years 1, 2, 3
            deadline = timezone.now() + timedelta(days=random.randint(7, 30))
            
            cls, created = Class.objects.get_or_create(
                name=course_info["name"],
                teacher=teacher,
                year=year,
                defaults={
                    "deadline": deadline,
                    "description": course_info["description"]
                }
            )
            
            # Update description if class already exists but has no description
            if not created and not cls.description:
                cls.description = course_info["description"]
                cls.save()
            
            classes.append(cls)
            if created:
                self.stdout.write(f"  Created: {cls}")

        # Create students
        self.stdout.write("Creating students...")
        students = []
        for i in range(1, 16):
            username = f"student{i}"
            if User.objects.filter(username=username).exists():
                student = User.objects.get(username=username)
            else:
                student = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password="student123",
                    first_name=f"Student",
                    last_name=f"{i}",
                    is_active=True
                )
            student.groups.add(student_group)
            
            # Assign year (distribute across years 1-3)
            year = ((i - 1) % 3) + 1
            Profile.objects.update_or_create(
                user=student,
                defaults={"student_year": year}
            )
            students.append(student)

        # Enroll students in classes matching their year
        self.stdout.write("Creating enrollments...")
        enrollment_count = 0
        for student in students:
            profile = Profile.objects.get(user=student)
            if profile.student_year:
                # Get classes for student's year
                year_classes = [c for c in classes if c.year == profile.student_year]
                # Enroll in 2-4 random classes from their year
                num_enrollments = min(random.randint(2, 4), len(year_classes))
                for cls in random.sample(year_classes, num_enrollments):
                    _, created = Enrollment.objects.get_or_create(
                        student=student,
                        class_ref=cls
                    )
                    if created:
                        enrollment_count += 1

        self.stdout.write(f"  Created {enrollment_count} enrollments")

        # Create submissions (some students submit to some classes)
        self.stdout.write("Creating submissions with files...")
        submission_count = 0
        for enrollment in Enrollment.objects.all():
            # 70% chance of having a submission
            if random.random() < 0.7:
                status = random.choices(
                    ["P", "A", "R"],
                    weights=[0.4, 0.5, 0.1]  # 40% pending, 50% approved, 10% rejected
                )[0]
                
                if not Submission.objects.filter(
                    student=enrollment.student,
                    class_ref=enrollment.class_ref
                ).exists():
                    # Choose file type and generate content
                    file_type = random.choice(["txt", "txt", "txt", "py"])  # 75% txt, 25% py
                    extension = file_type
                    
                    content = self.generate_file_content(
                        file_type,
                        enrollment.student.username,
                        enrollment.class_ref.name
                    )
                    
                    # Create filename
                    filename = f"assignment.{extension}"
                    
                    # Create submission with file
                    submission = Submission.objects.create(
                        student=enrollment.student,
                        class_ref=enrollment.class_ref,
                        status=status,
                        feedback="" if status == "P" else f"{'Good work!' if status == 'A' else 'Please revise and resubmit'}"
                    )
                    
                    # Attach the file
                    submission.file.save(
                        filename,
                        ContentFile(content.encode('utf-8')),
                        save=True
                    )
                    submission_count += 1

        self.stdout.write(f"  Created {submission_count} submissions with files")

        # Summary
        self.stdout.write(self.style.SUCCESS("\n✓ Seeded demo data successfully!"))
        self.stdout.write(self.style.SUCCESS(f"  Teachers: {len(teachers)}"))
        self.stdout.write(self.style.SUCCESS(f"  Students: {len(students)}"))
        self.stdout.write(self.style.SUCCESS(f"  Classes: {len(classes)}"))
        self.stdout.write(self.style.SUCCESS(f"  Enrollments: {enrollment_count}"))
        self.stdout.write(self.style.SUCCESS(f"  Submissions: {submission_count}"))
        self.stdout.write(self.style.WARNING("\nDemo credentials:"))
        self.stdout.write("  Teachers: teacher1-3 / teacher123")
        self.stdout.write("  Students: student1-15 / student123")
