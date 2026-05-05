from django.core.management.base import BaseCommand
from portal.models import Teacher

class Command(BaseCommand):
    help = 'Create a test teacher account for testing login functionality'

    def handle(self, *args, **options):
        # Check if teacher already exists
        teacher_id = 'TCH12345678'
        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            self.stdout.write(self.style.WARNING(f'Teacher with ID {teacher_id} already exists'))
            return

        # Create test teacher
        from datetime import date
        teacher = Teacher.objects.create(
            teacher_id=teacher_id,
            pin='123456',
            first_name='Test',
            last_name='Teacher',
            gender='male',
            email='teacher@school.com',
            phone='0123456789',
            address='123 Test Street',
            date_of_birth=date(1980, 1, 1)
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test teacher:\n'
                f'Teacher ID: {teacher_id}\n'
                f'PIN: 123456\n'
                f'Name: Test Teacher\n'
                f'Email: teacher@school.com'
            )
        )
