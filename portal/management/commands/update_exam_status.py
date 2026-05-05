from django.core.management.base import BaseCommand
from django.db import transaction
from portal.models import Learner, ExamStatus, Registration
from datetime import datetime

class Command(BaseCommand):
    help = 'Update exam status to NA for all registered learners for current term'

    def handle(self, *args, **options):
        current_year = datetime.now().year
        current_term = 2  # Term 2 as requested
        
        self.stdout.write(f'Updating exam status to NA for Term {current_term}, {current_year}...')
        
        updated_count = 0
        created_count = 0
        
        # Get all learners with registrations
        learners_with_registrations = Learner.objects.filter(
            registrations__isnull=False
        ).distinct()
        
        self.stdout.write(f'Found {learners_with_registrations.count()} learners with registrations')
        
        with transaction.atomic():
            for learner in learners_with_registrations:
                # Get learner's registered subjects
                registrations = learner.registrations.all()
                
                for registration in registrations:
                    subjects_str = registration.subjects
                    if subjects_str:
                        subjects = [s.strip() for s in subjects_str.split(',') if s.strip()]
                        
                        for subject in subjects:
                            # Create or update exam status to NA
                            exam_status, created = ExamStatus.objects.get_or_create(
                                learner=learner,
                                subject=subject,
                                academic_year=current_year,
                                term=current_term,
                                defaults={'status': 'na'}
                            )
                            
                            if created:
                                created_count += 1
                                self.stdout.write(
                                    f'Created NA status for {learner.full_name} - {subject}'
                                )
                            elif exam_status.status != 'na':
                                exam_status.status = 'na'
                                exam_status.save()
                                updated_count += 1
                                self.stdout.write(
                                    f'Updated status to NA for {learner.full_name} - {subject}'
                                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated exam statuses:\n'
                f'- Created: {created_count} new records\n'
                f'- Updated: {updated_count} existing records\n'
                f'- Total: {created_count + updated_count} records set to NA'
            )
        )
