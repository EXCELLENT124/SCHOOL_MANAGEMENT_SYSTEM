from django.core.management.base import BaseCommand
from portal.models import Grade, Stream, Subject


class Command(BaseCommand):
    help = 'Initialize default grades, streams, and subjects for the school'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating default grades...')
        
        # Create grades 8-12
        grades_created = 0
        for grade_num in range(8, 13):
            grade, created = Grade.objects.get_or_create(
                grade_number=grade_num,
                year=2024,
                defaults={
                    'grade_name': f'Grade {grade_num}',
                    'capacity': 30,
                    'available_spaces': 30,
                    'description': f'Grade {grade_num} - Secondary School'
                }
            )
            if created:
                grades_created += 1
                self.stdout.write(f'  Created {grade}')
            else:
                self.stdout.write(f'  {grade} already exists')
        
        self.stdout.write(f'\nCreated {grades_created} new grades')
        
        # Create subjects first
        self.stdout.write('\nCreating default subjects...')
        
        all_subjects_data = [
            # Core subjects
            {'name': 'English', 'description': 'First Additional Language'},
            {'name': 'Home Language', 'description': 'Mother tongue language'},
            {'name': 'Mathematics', 'description': 'Core mathematics subject'},
            {'name': 'Mathematical Literacy', 'description': 'Practical mathematics for everyday life'},
            
            # Science subjects
            {'name': 'Physical Sciences', 'description': 'Physics and Chemistry combined'},
            {'name': 'Life Sciences', 'description': 'Biology and life processes'},
            
            # Commercial subjects
            {'name': 'Accounting', 'description': 'Financial record keeping and reporting'},
            {'name': 'Business Studies', 'description': 'Business management and entrepreneurship'},
            {'name': 'Economics', 'description': 'Study of production, distribution, and consumption'},
            
            # General/Humanities subjects
            {'name': 'History', 'description': 'Study of past events and human civilization'},
            {'name': 'Geography', 'description': 'Study of Earth and its features'},
            {'name': 'Visual Arts', 'description': 'Creative arts and design'},
            {'name': 'Tourism', 'description': 'Travel and tourism industry studies'},
            {'name': 'Computer Applications Technology', 'description': 'IT and computer skills'},
            {'name': 'Life Orientation', 'description': 'Personal development and citizenship'},
        ]
        
        subjects_created = 0
        subject_objects = {}
        for subject_data in all_subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=subject_data['name'],
                defaults={
                    'description': subject_data['description'],
                    'is_active': True
                }
            )
            subject_objects[subject.name] = subject
            if created:
                subjects_created += 1
                self.stdout.write(f'  Created subject: {subject}')
            else:
                self.stdout.write(f'  Subject exists: {subject}')
        
        self.stdout.write(f'\nCreated {subjects_created} new subjects')
        
        # Create streams with subject relationships
        self.stdout.write('\nCreating default streams...')
        
        streams_data = [
            {
                'code': 'science',
                'name': 'Science Stream',
                'description': 'For students interested in science, technology, engineering, and mathematics. Ideal for careers in medicine, engineering, and scientific research.',
                'subject_names': [
                    'English', 'Home Language', 'Mathematics', 'Physical Sciences', 
                    'Life Sciences', 'Geography', 'Computer Applications Technology', 'Life Orientation'
                ]
            },
            {
                'code': 'commercial',
                'name': 'Commercial Stream',
                'description': 'For students interested in business, economics, and accounting. Ideal for careers in business, finance, and management.',
                'subject_names': [
                    'English', 'Home Language', 'Mathematics', 'Mathematical Literacy',
                    'Accounting', 'Business Studies', 'Economics', 'Life Orientation'
                ]
            },
            {
                'code': 'general',
                'name': 'General Stream',
                'description': 'For students interested in arts, humanities, and general studies. Offers a balanced curriculum with diverse subject options.',
                'subject_names': [
                    'English', 'Home Language', 'Mathematics', 'Mathematical Literacy',
                    'History', 'Geography', 'Visual Arts', 'Tourism', 'Life Orientation'
                ]
            }
        ]
        
        streams_created = 0
        for stream_data in streams_data:
            stream, created = Stream.objects.get_or_create(
                code=stream_data['code'],
                defaults={
                    'name': stream_data['name'],
                    'description': stream_data['description'],
                    'subjects_text': ', '.join(stream_data['subject_names'])
                }
            )
            
            # Link subjects to stream
            for subject_name in stream_data['subject_names']:
                if subject_name in subject_objects:
                    stream.subjects.add(subject_objects[subject_name])
            
            if created:
                streams_created += 1
                self.stdout.write(f'  Created {stream} with {stream.subjects.count()} subjects')
            else:
                self.stdout.write(f'  {stream} already exists, updated subjects')
        
        self.stdout.write(f'\nCreated {streams_created} new streams')
        self.stdout.write(self.style.SUCCESS('\nInitialization complete!'))
