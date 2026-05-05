from django.core.management.base import BaseCommand
from django.utils import timezone
from portal.models import Learner

class Command(BaseCommand):
    help = 'Create a test learner account for testing login functionality'

    def handle(self, *args, **options):
        # Check if learner already exists
        study_number = 'STU12345678'
        if Learner.objects.filter(study_number=study_number).exists():
            self.stdout.write(self.style.WARNING(f'Learner with study number {study_number} already exists'))
            return

        # Create test learner
        from portal.models import Grade
        grade = Grade.objects.get(grade_number=10, year=timezone.now().year)
        learner = Learner.objects.create(
            study_number=study_number,
            pin='123456',
            first_name='Test',
            last_name='Learner',
            gender='male',
            email='learner@school.com',
            phone='0123456789',
            address='123 Test Street',
            date_of_birth='2005-01-01',
            grade=grade
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test learner:\n'
                f'Study Number: {study_number}\n'
                f'PIN: 123456\n'
                f'Name: Test Learner\n'
                f'Grade: 10\n'
                f'Email: learner@school.com'
            )
        )
