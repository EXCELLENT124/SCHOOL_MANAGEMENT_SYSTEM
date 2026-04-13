from django import forms
from django.core.validators import FileExtensionValidator
from .models import Application, Document, Registration, Grade


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
        
        # If this is a new registration, require rules acceptance
        if not self.instance.pk and not accept_rules:
            self.add_error('accept_rules', 'You must accept the rules and regulations to complete registration.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert selected subjects list to comma-separated string
        selected_subjects = self.cleaned_data.get('selected_subjects', [])
        instance.subjects = ', '.join(selected_subjects)
        if commit:
            instance.save()
        return instance


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
    
    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        confirm_pin = cleaned_data.get('confirm_pin')
        
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
