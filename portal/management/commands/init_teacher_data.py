from django.core.management.base import BaseCommand
from django.utils import timezone
from portal.models import Teacher, Task, Subject, Grade
import uuid

def generate_teacher_pin():
    """Generate a 6-digit PIN for teachers."""
    return f"{uuid.uuid4().int % 900000 + 100000}"

class Command(BaseCommand):
    help = 'Initialize sample teachers and tasks for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample teachers...')
        
        # Get subjects and grades
        subjects = Subject.objects.filter(is_active=True)
        grades = Grade.objects.all()
        
        if not subjects.exists():
            self.stdout.write(self.style.WARNING('No subjects found. Please run init_data first.'))
            return
        
        if not grades.exists():
            self.stdout.write(self.style.WARNING('No grades found. Please run init_data first.'))
            return
        
        # Create sample teachers
        teachers_data = [
            {
                'first_name': 'John',
                'last_name': 'Smith',
                'date_of_birth': '1980-05-15',
                'gender': 'male',
                'email': 'john.smith@school.edu',
                'phone': '+27 12 345 6789',
                'address': '123 School Street, Johannesburg',
                'employee_number': 'EMP001',
                'subjects': ['Mathematics', 'Physical Sciences'],
                'grades': ['Grade 10', 'Grade 11', 'Grade 12']
            },
            {
                'first_name': 'Mary',
                'last_name': 'Johnson',
                'date_of_birth': '1985-08-22',
                'gender': 'female',
                'email': 'mary.johnson@school.edu',
                'phone': '+27 12 345 6790',
                'address': '456 Education Ave, Johannesburg',
                'employee_number': 'EMP002',
                'subjects': ['English', 'History'],
                'grades': ['Grade 8', 'Grade 9', 'Grade 10']
            },
            {
                'first_name': 'Robert',
                'last_name': 'Williams',
                'date_of_birth': '1978-12-10',
                'gender': 'male',
                'email': 'robert.williams@school.edu',
                'phone': '+27 12 345 6791',
                'address': '789 Learning Rd, Johannesburg',
                'employee_number': 'EMP003',
                'subjects': ['Life Sciences', 'Geography'],
                'grades': ['Grade 10', 'Grade 11', 'Grade 12']
            }
        ]
        
        created_teachers = []
        for teacher_data in teachers_data:
            # Extract subjects and grades
            subject_names = teacher_data.pop('subjects')
            grade_names = teacher_data.pop('grades')
            
            # Create teacher
            teacher, created = Teacher.objects.get_or_create(
                email=teacher_data['email'],
                defaults=teacher_data
            )
            
            if created:
                # Generate PIN
                teacher.pin = generate_teacher_pin()
                teacher.save()
                
                # Add subjects
                for subject_name in subject_names:
                    try:
                        subject = Subject.objects.get(name=subject_name)
                        teacher.subjects.add(subject)
                    except Subject.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'Subject "{subject_name}" not found'))
                
                # Add grades
                for grade_name in grade_names:
                    try:
                        grade = Grade.objects.get(grade_name=grade_name)
                        teacher.grades.add(grade)
                    except Grade.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'Grade "{grade_name}" not found'))
                
                created_teachers.append(teacher)
                self.stdout.write(f'  Created teacher: {teacher.full_name} (ID: {teacher.teacher_id}, PIN: {teacher.pin})')
            else:
                self.stdout.write(f'  Teacher already exists: {teacher.full_name}')
        
        # Create sample tasks
        self.stdout.write('\nCreating sample tasks...')
        
        if created_teachers:
            tasks_data = [
                {
                    'teacher': created_teachers[0],  # John Smith
                    'title': 'Mathematics Assignment 1',
                    'description': 'Complete exercises 1-20 from Chapter 5',
                    'task_type': 'assignment',
                    'content_type': 'text',
                    'text_content': 'Please solve all problems showing your work clearly. Pay special attention to word problems.',
                    'subject': Subject.objects.get(name='Mathematics'),
                    'grade': Grade.objects.get(grade_name='Grade 10'),
                    'total_marks': 100,
                    'due_date': timezone.now() + timezone.timedelta(days=7)
                },
                {
                    'teacher': created_teachers[0],  # John Smith
                    'title': 'Physics Quiz - Forces',
                    'description': 'Quiz on Newton\'s Laws of Motion',
                    'task_type': 'quiz',
                    'content_type': 'pdf',
                    'subject': Subject.objects.get(name='Physical Sciences'),
                    'grade': Grade.objects.get(grade_name='Grade 11'),
                    'total_marks': 50,
                    'due_date': timezone.now() + timezone.timedelta(days=3)
                },
                {
                    'teacher': created_teachers[1],  # Mary Johnson
                    'title': 'English Essay - My Hero',
                    'description': 'Write a 500-word essay about your hero',
                    'task_type': 'assignment',
                    'content_type': 'mixed',
                    'text_content': 'Write a well-structured essay of at least 500 words about someone you consider to be a hero. Include an introduction, 3 body paragraphs, and a conclusion.',
                    'subject': Subject.objects.get(name='English'),
                    'grade': Grade.objects.get(grade_name='Grade 9'),
                    'total_marks': 100,
                    'due_date': timezone.now() + timezone.timedelta(days=10)
                },
                {
                    'teacher': created_teachers[2],  # Robert Williams
                    'title': 'Biology Project - Cell Structure',
                    'description': 'Create a model of a plant or animal cell',
                    'task_type': 'project',
                    'content_type': 'mixed',
                    'text_content': 'Create a detailed model of either a plant or animal cell. Label all major organelles and include a brief description of their functions.',
                    'subject': Subject.objects.get(name='Life Sciences'),
                    'grade': Grade.objects.get(grade_name='Grade 10'),
                    'total_marks': 150,
                    'due_date': timezone.now() + timezone.timedelta(days=14)
                }
            ]
            
            for task_data in tasks_data:
                task = Task.objects.create(**task_data)
                self.stdout.write(f'  Created task: {task.title}')
        
        self.stdout.write(self.style.SUCCESS('\nTeacher data initialization complete!'))
        self.stdout.write('\nLogin credentials:')
        for teacher in created_teachers:
            self.stdout.write(f'  {teacher.full_name}: ID={teacher.teacher_id}, PIN={teacher.pin}')
