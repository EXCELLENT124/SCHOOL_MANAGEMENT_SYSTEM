from django import forms
from django.core.validators import FileExtensionValidator
from .models import Application, Document, Registration, Grade, Learner, Teacher, Exam, Subject, Task, TaskSubmission


class ApplicationForm(forms.ModelForm):
    """Form for admission application."""
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Learner Date of Birth'
    )
    
    parent_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'parent@example.com'}),
        label='Parent/Guardian Email'
    )
    
    parent_phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+27 12 345 6789'}),
        label='Parent/Guardian Phone'
    )
    
    emergency_contact = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+27 12 345 6789'}),
        label='Emergency Contact Phone'
    )
    
    class Meta:
        model = Application
        fields = [
            'learner_name', 'date_of_birth', 'gender', 'grade_applying',
            'previous_school', 'previous_grade',
            'parent_name', 'parent_email', 'parent_phone', 'parent_address',
            'emergency_contact', 'emergency_contact_name'
        ]
        widgets = {
            'learner_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name of Learner'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'grade_applying': forms.Select(attrs={'class': 'form-control'}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of Previous School (if any)'}),
            'previous_grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Previous Grade Completed'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name of Parent/Guardian'}),
            'parent_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Home Address'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter grades to only show those with available spaces
        self.fields['grade_applying'].queryset = Grade.objects.filter(available_spaces__gt=0)


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""
    
    file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        label='Select Document'
    )
    
    class Meta:
        model = Document
        fields = ['document_type', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
        }


class LearnerLoginForm(forms.Form):
    """Form for learner login."""
    
    study_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Study Number (e.g., STU12345678)',
            'autocomplete': 'off'
        }),
        label='Study Number'
    )
    
    pin = forms.CharField(
        max_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your 6-digit PIN',
            'maxlength': '6'
        }),
        label='PIN'
    )


class RegistrationForm(forms.ModelForm):
    """Form for academic registration with stream-based subject selection."""
    
    accept_rules = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I accept the rules and regulations'
    )

    scholarship_choice = forms.ChoiceField(
        choices=[('no', 'No'), ('yes', 'Yes')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Scholarship or Bursary',
        initial='no',
        required=False,
        help_text='Select Yes if you have a scholarship.'
    )

    scholarship_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter scholarship name if applicable'
        }),
        label='Scholarship Name'
    )

    bursary_choice = forms.ChoiceField(
        choices=[('no', 'No'), ('yes', 'Yes')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Do you have a bursary?',
        initial='no',
        required=False,
        help_text='Select Yes if you have a bursary.'
    )

    bursary_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter bursary name if applicable'
        }),
        label='Bursary Name'
    )
    
    # Dynamic subjects field - will be populated based on stream
    selected_subjects = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Select Subjects',
        choices=[],  # Will be populated dynamically
        help_text='Please select at least 4 subjects'
    )
    
    class Meta:
        model = Registration
        fields = ['stream']
        widgets = {
            'stream': forms.Select(attrs={'class': 'form-control', 'id': 'stream-select'}),
        }
    
    def __init__(self, *args, available_subjects=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate subjects choices if available
        if available_subjects:
            self.fields['selected_subjects'].choices = [
                (subject.strip(), subject.strip()) 
                for subject in available_subjects 
                if subject.strip()
            ]
        
        # Set initial values if editing existing registration
        if self.instance and self.instance.pk and self.instance.subjects:
            current_subjects = [s.strip() for s in self.instance.subjects.split(',') if s.strip()]
            self.initial['selected_subjects'] = current_subjects
    
    def clean_selected_subjects(self):
        subjects = self.cleaned_data.get('selected_subjects', [])
        if len(subjects) < 4:
            raise forms.ValidationError('Please select at least 4 subjects.')
        if len(subjects) > 8:
            raise forms.ValidationError('You can select a maximum of 8 subjects.')
        return subjects
    
    def clean(self):
        cleaned_data = super().clean()
        accept_rules = cleaned_data.get('accept_rules')
        scholarship_choice = cleaned_data.get('scholarship_choice')
        scholarship_name = cleaned_data.get('scholarship_name', '').strip()
        bursary_choice = cleaned_data.get('bursary_choice')
        bursary_name = cleaned_data.get('bursary_name', '').strip()
        
        # If this is a new registration, require rules acceptance
        if not self.instance.pk and not accept_rules:
            self.add_error('accept_rules', 'You must accept the rules and regulations to complete registration.')

        if scholarship_choice == 'yes' and not scholarship_name:
            self.add_error('scholarship_name', 'Please enter the scholarship name.')

        if bursary_choice == 'yes' and not bursary_name:
            self.add_error('bursary_name', 'Please enter the bursary name.')
        
        return cleaned_data


class TeacherLoginForm(forms.Form):
    """Form for teacher login."""
    teacher_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Teacher ID (e.g., TCH12345678)',
            'autofocus': 'autofocus'
        }),
        label='Teacher ID'
    )
    pin = forms.CharField(
        max_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your 6-digit PIN'
        }),
        label='PIN'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        teacher_id = cleaned_data.get('teacher_id')
        pin = cleaned_data.get('pin')
        
        if teacher_id and pin:
            from .models import Teacher
            try:
                teacher = Teacher.objects.get(teacher_id=teacher_id, pin=pin, is_active=True)
                cleaned_data['teacher'] = teacher
            except Teacher.DoesNotExist:
                raise forms.ValidationError('Invalid Teacher ID or PIN. Please try again.')
        
        return cleaned_data


class TaskForm(forms.ModelForm):
    """Form for creating and editing tasks."""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'task_type', 'content_type', 
            'grade', 'subject', 'text_content', 'attachment', 
            'due_date', 'total_marks'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'task_type': forms.Select(attrs={'class': 'form-control'}),
            'content_type': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'text_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '1000'}),
        }
    
    def __init__(self, teacher=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            # Filter grades and subjects based on teacher's assignments
            self.fields['grade'].queryset = teacher.grades.all()
            self.fields['subject'].queryset = teacher.subjects.all()
        
        # Add help text
        self.fields['content_type'].help_text = "Choose how you want to present the task content"
        self.fields['attachment'].help_text = "Upload PDF or image file (optional)"
        self.fields['due_date'].help_text = "Set the deadline for task submission"
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date:
            from django.utils import timezone
            if due_date <= timezone.now():
                raise forms.ValidationError("Due date must be in the future.")
        return due_date
    
    def clean_total_marks(self):
        marks = self.cleaned_data.get('total_marks')
        if marks and marks < 1:
            raise forms.ValidationError("Total marks must be at least 1.")
        return marks


class TaskSubmissionForm(forms.ModelForm):
    """Form for learners to submit tasks."""
    
    class Meta:
        model = TaskSubmission
        fields = ['text_response', 'attachment']
        widgets = {
            'text_response': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 8,
                'placeholder': 'Type your response here...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            })
        }
    
    def __init__(self, task=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if task:
            # Adjust based on task content type
            if task.content_type == 'pdf':
                self.fields['text_response'].widget = forms.HiddenInput()
                self.fields['attachment'].required = True
                self.fields['attachment'].help_text = "Please upload your completed task (PDF, DOC, DOCX, JPG, PNG)"
            elif task.content_type == 'text':
                self.fields['text_response'].required = True
                self.fields['attachment'].widget = forms.HiddenInput()
                self.fields['text_response'].help_text = "Please type your response here"
            else:  # mixed
                self.fields['text_response'].help_text = "Type your response (optional if uploading file)"
                self.fields['attachment'].help_text = "Upload your work (PDF, DOC, DOCX, JPG, PNG - optional)"


class TaskGradingForm(forms.ModelForm):
    """Form for teachers to grade task submissions."""
    
    class Meta:
        model = TaskSubmission
        fields = ['marks_obtained', 'teacher_feedback']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.1'
            }),
            'teacher_feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide feedback on the submission...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.task:
            task = self.instance.task
            self.fields['marks_obtained'].widget.attrs['max'] = task.total_marks
            self.fields['marks_obtained'].label = f'Marks (out of {task.total_marks})'
    
    def clean_marks_obtained(self):
        marks = self.cleaned_data.get('marks_obtained')
        if marks is not None:
            if self.instance and self.instance.task:
                if marks > self.instance.task.total_marks:
                    raise forms.ValidationError(f"Marks cannot exceed total marks ({self.instance.task.total_marks}).")
                if marks < 0:
                    raise forms.ValidationError("Marks cannot be negative.")
        return marks
    
    def save(self, commit=True):
        submission = super().save(commit=False)
        if submission.marks_obtained is not None:
            submission.status = 'graded'
            from django.utils import timezone
            submission.graded_at = timezone.now()
        if commit:
            submission.save()
        return submission


class CreatePINForm(forms.Form):
    """Form for applicants to create their PIN."""
    
    application_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Application ID (e.g., APP12345678)',
            'autocomplete': 'off'
        }),
        label='Application ID'
    )
    
    pin = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit PIN',
            'maxlength': '6'
        }),
        label='Create PIN',
        help_text='PIN must be exactly 6 digits'
    )
    
    confirm_pin = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm 6-digit PIN',
            'maxlength': '6'
        }),
        label='Confirm PIN'
    )
    
    def clean_application_id(self):
        application_id = self.cleaned_data['application_id'].upper().strip()
        try:
            application = Application.objects.get(application_id=application_id)
            # Check if learner already exists for this application
            if hasattr(application, 'learner_profile') and application.learner_profile:
                raise forms.ValidationError('A PIN has already been created for this application. Please login with your Study Number and PIN.')
        except Application.DoesNotExist:
            raise forms.ValidationError('Application ID not found. Please check and try again.')
        return application_id
    
    def clean_pin(self):
        pin = self.cleaned_data['pin']
        if not pin.isdigit():
            raise forms.ValidationError('PIN must contain only numbers.')
        return pin
    
class CreateTeacherPINForm(forms.Form):
    """Form for creating teacher PIN."""
    
    teacher_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Teacher ID (e.g., TCH12345678)',
            'autocomplete': 'off'
        }),
        label='Teacher ID'
    )
    
    pin = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit PIN',
            'maxlength': '6'
        }),
        label='Create PIN',
        help_text='PIN must be exactly 6 digits'
    )
    
    confirm_pin = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm 6-digit PIN',
            'maxlength': '6'
        }),
        label='Confirm PIN'
    )
    
    def clean_teacher_id(self):
        teacher_id = self.cleaned_data['teacher_id'].upper().strip()
        try:
            teacher = Teacher.objects.get(teacher_id=teacher_id)
            # Check if teacher already has a PIN set (not the default generated one)
            if teacher.pin and len(teacher.pin) == 6 and teacher.pin.isdigit():
                raise forms.ValidationError('A PIN has already been created for this teacher.')
        except Teacher.DoesNotExist:
            raise forms.ValidationError('Teacher ID not found. Please check and try again.')
        return teacher_id
    
    def clean_pin(self):
        pin = self.cleaned_data['pin']
        if not pin.isdigit():
            raise forms.ValidationError('PIN must contain only numbers.')
        return pin
    
    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        confirm_pin = cleaned_data.get('confirm_pin')
        
        if pin and confirm_pin and pin != confirm_pin:
            raise forms.ValidationError('PINs do not match.')
        
        return cleaned_data
        
        if pin and confirm_pin and pin != confirm_pin:
            self.add_error('confirm_pin', 'PINs do not match.')
        
        return cleaned_data


class StudentEnquiryForm(forms.Form):
    """Form for student enquiries."""
    
    enquiry_type = forms.ChoiceField(
        choices=[
            ('academic', 'Academic Query'),
            ('financial', 'Financial Query'),
            ('registration', 'Registration Query'),
            ('general', 'General Enquiry'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Type of Enquiry'
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject of your enquiry'}),
        label='Subject'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe your enquiry in detail...'
        }),
        label='Message'
    )


class SubmitMarksForm(forms.ModelForm):
    """Form for teachers to submit learner marks."""
    
    learner = forms.ModelChoiceField(
        queryset=Learner.objects.filter(admission_status='registered'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Learner'
    )
    
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Subject'
    )
    
    exam_type = forms.ChoiceField(
        choices=Exam.EXAM_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Exam Type'
    )
    
    marks = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Enter marks (0-100)'
        }),
        label='Marks'
    )
    
    date_taken = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Date Taken'
    )
    
    teacher_remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional remarks about the learner\'s performance'
        }),
        label='Remarks'
    )
    
    class Meta:
        model = Exam
        fields = ['learner', 'subject', 'exam_type', 'marks', 'date_taken', 'teacher_remarks']
    
    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            # Filter learners to only those in grades the teacher teaches
            taught_grades = teacher.grades.all()
            if taught_grades:
                self.fields['learner'].queryset = Learner.objects.filter(
                    grade__in=taught_grades,
                    admission_status='registered'
                )
            # Filter subjects to only those the teacher teaches
            self.fields['subject'].queryset = teacher.subjects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        learner = cleaned_data.get('learner')
        subject = cleaned_data.get('subject')
        exam_type = cleaned_data.get('exam_type')
        date_taken = cleaned_data.get('date_taken')
        
        if learner and subject and exam_type and date_taken:
            # Check if this exam already exists
            existing_exam = Exam.objects.filter(
                learner=learner,
                subject=subject.name,  # subject is a Subject instance, but Exam.subject is CharField
                exam_type=exam_type,
                date_taken=date_taken
            ).exists()
            
            if existing_exam:
                raise forms.ValidationError('An exam record already exists for this learner, subject, exam type, and date.')
        
        return cleaned_data
    
    def save(self, commit=True, teacher=None):
        instance = super().save(commit=False)
        if teacher:
            instance.teacher = teacher
        # Convert subject instance to string for Exam model
        instance.subject = self.cleaned_data['subject'].name
        if commit:
            instance.save()
        return instance
