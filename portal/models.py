import os
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


def generate_study_number():
    """Generate a unique study number for learners."""
    return f"STU{uuid.uuid4().hex[:8].upper()}"


def generate_pin():
    """Generate a 6-digit PIN for learners."""
    return f"{uuid.uuid4().int % 900000 + 100000}"


def generate_application_id():
    """Generate a unique application ID."""
    return f"APP{uuid.uuid4().hex[:8].upper()}"


def document_upload_path(instance, filename):
    """Custom upload path for documents."""
    ext = filename.split('.')[-1]
    return f'documents/{instance.application.application_id}/{instance.document_type}_{timezone.now().strftime("%Y%m%d")}.{ext}'


class Grade(models.Model):
    """Grade/Class model to track capacity and available spaces."""
    GRADE_CHOICES = [
        (8, 'Grade 8'),
        (9, 'Grade 9'),
        (10, 'Grade 10'),
        (11, 'Grade 11'),
        (12, 'Grade 12'),
    ]
    
    grade_number = models.IntegerField(choices=GRADE_CHOICES)
    grade_name = models.CharField(max_length=50)
    capacity = models.IntegerField(default=30, validators=[MinValueValidator(1)])
    available_spaces = models.IntegerField(default=30)
    year = models.IntegerField(default=timezone.now().year)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['grade_number', 'year']
        ordering = ['grade_number']
    
    def __str__(self):
        return f"{self.grade_name} - {self.year} (Available: {self.available_spaces}/{self.capacity})"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.available_spaces = self.capacity
        super().save(*args, **kwargs)


class Subject(models.Model):
    """Individual subject model for better management."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.name.upper().replace(' ', '_')[:20]
        super().save(*args, **kwargs)


class Stream(models.Model):
    """Academic stream choices (Science, Commercial, General)."""
    STREAM_CHOICES = [
        ('science', 'Science Stream'),
        ('commercial', 'Commercial Stream'),
        ('general', 'General Stream'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    subjects = models.ManyToManyField(Subject, related_name='streams', blank=True)
    subjects_text = models.TextField(help_text="Legacy: List of main subjects in this stream", blank=True)
    
    def __str__(self):
        return self.name
    
    def get_subject_list(self):
        """Get list of subject names for this stream."""
        if self.subjects.exists():
            return list(self.subjects.filter(is_active=True).values_list('name', flat=True))
        elif self.subjects_text:
            return [s.strip() for s in self.subjects_text.split(',') if s.strip()]
        return []


class Application(models.Model):
    """Application model for new learners."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    application_id = models.CharField(max_length=20, unique=True, default=generate_application_id, editable=False)
    study_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Learner Information
    learner_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    grade_applying = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='applications')
    previous_school = models.CharField(max_length=200, blank=True)
    previous_grade = models.CharField(max_length=50, blank=True)
    
    # Parent/Guardian Information
    parent_name = models.CharField(max_length=200)
    parent_email = models.EmailField()
    parent_phone = models.CharField(max_length=20)
    parent_address = models.TextField()
    emergency_contact = models.CharField(max_length=20)
    emergency_contact_name = models.CharField(max_length=200)
    
    # Application Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)
    review_notes = models.TextField(blank=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.application_id} - {self.learner_name} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Generate study number when application is accepted
        if self.status == 'accepted' and not self.study_number:
            self.study_number = generate_study_number()
            self.decision_date = timezone.now()
        super().save(*args, **kwargs)


class Document(models.Model):
    """Uploaded documents for applications."""
    DOCUMENT_TYPES = [
        ('birth_certificate', 'Birth Certificate'),
        ('previous_report', 'Previous Year Progress Report'),
        ('id_document', 'ID/Passport Document'),
        ('proof_residence', 'Proof of Residence'),
        ('immunization', 'Immunization Records'),
        ('other', 'Other Document'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to=document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.document_type} - {self.application.learner_name}"
    
    def filename(self):
        return os.path.basename(self.file.name)


class Learner(models.Model):
    """Registered learner model."""
    ADMISSION_STATUS = [
        ('applied', 'Applied'),
        ('admitted', 'Admitted'),
        ('registered', 'Registered'),
        ('suspended', 'Suspended'),
        ('expelled', 'Expelled'),
        ('transferred', 'Transferred'),
        ('graduated', 'Graduated'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    study_number = models.CharField(max_length=20, unique=True, default=generate_study_number, editable=False)
    pin = models.CharField(max_length=6, default=generate_pin, editable=False)
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    
    # Academic Information
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, related_name='learners')
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True, related_name='learners')
    admission_status = models.CharField(max_length=20, choices=ADMISSION_STATUS, default='applied')
    date_joined = models.DateField(auto_now_add=True)
    
    # Parent Information
    parent_name = models.CharField(max_length=200)
    parent_email = models.EmailField()
    parent_phone = models.CharField(max_length=20)
    
    # Application Reference
    application = models.OneToOneField(Application, on_delete=models.SET_NULL, null=True, blank=True, related_name='learner_profile')
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.study_number} - {self.first_name} {self.last_name}"
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Exam(models.Model):
    """Exam records for learners."""
    EXAM_TYPES = [
        ('midterm', 'Mid-Term Examination'),
        ('final', 'Final Examination'),
        ('test', 'Class Test'),
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('practical', 'Practical Examination'),
    ]
    
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='exams')
    subject = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    marks = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade = models.CharField(max_length=2)  # A, B, C, etc.
    year = models.IntegerField()
    term = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    date_taken = models.DateField()
    teacher_remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_taken', 'subject']
    
    def __str__(self):
        return f"{self.learner} - {self.subject} ({self.exam_type})"
    
    def save(self, *args, **kwargs):
        # Calculate grade based on marks
        if self.marks >= 80:
            self.grade = 'A'
        elif self.marks >= 70:
            self.grade = 'B'
        elif self.marks >= 60:
            self.grade = 'C'
        elif self.marks >= 50:
            self.grade = 'D'
        elif self.marks >= 40:
            self.grade = 'E'
        else:
            self.grade = 'F'
        super().save(*args, **kwargs)


class Registration(models.Model):
    """Academic registration for learners."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('incomplete', 'Incomplete'),
    ]
    
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='registrations')
    academic_year = models.IntegerField()
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='registrations')
    subjects = models.TextField(help_text="Selected subjects")
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rules_accepted = models.BooleanField(default=False)
    rules_accepted_date = models.DateTimeField(null=True, blank=True)
    
    # Registration fees
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Proof of registration (PDF)
    proof_of_registration = models.FileField(upload_to='registration_proofs/', null=True, blank=True)
    
    class Meta:
        unique_together = ['learner', 'academic_year']
        ordering = ['-academic_year']
    
    def __str__(self):
        return f"{self.learner} - {self.academic_year} Registration"


class FinancialInfo(models.Model):
    """Financial information for learners."""
    SCHOLARSHIP_STATUS = [
        ('none', 'No Scholarship'),
        ('partial', 'Partial Scholarship'),
        ('full', 'Full Scholarship'),
    ]
    
    BURSARY_STATUS = [
        ('none', 'No Bursary'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_STATUS = [
        ('paid', 'Fully Paid'),
        ('partial', 'Partially Paid'),
        ('unpaid', 'Unpaid'),
        ('overdue', 'Overdue'),
    ]
    
    learner = models.OneToOneField(Learner, on_delete=models.CASCADE, related_name='financial_info')
    tuition_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Scholarship Information
    scholarship_status = models.CharField(max_length=20, choices=SCHOLARSHIP_STATUS, default='none')
    scholarship_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    scholarship_details = models.TextField(blank=True)
    
    # Bursary Information
    bursary_status = models.CharField(max_length=20, choices=BURSARY_STATUS, default='none')
    bursary_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bursary_details = models.TextField(blank=True)
    
    # Payment Information
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    last_payment_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Financial Information'
        verbose_name_plural = 'Financial Information'
    
    def __str__(self):
        return f"{self.learner} - Financial Info"
    
    def save(self, *args, **kwargs):
        # Calculate balance
        total_deductions = self.scholarship_amount + self.bursary_amount
        self.balance_due = self.tuition_fees - total_deductions - self.total_paid
        
        # Update payment status
        if self.balance_due <= 0:
            self.payment_status = 'paid'
        elif self.total_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
        
        super().save(*args, **kwargs)


class ProgressReport(models.Model):
    """Progress reports for learners."""
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='progress_reports')
    year = models.IntegerField()
    term = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    overall_average = models.DecimalField(max_digits=5, decimal_places=2)
    class_position = models.IntegerField(null=True, blank=True)
    total_learners = models.IntegerField(null=True, blank=True)
    teacher_comments = models.TextField()
    principal_comments = models.TextField(blank=True)
    report_file = models.FileField(upload_to='progress_reports/', null=True, blank=True)
    date_issued = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ['learner', 'year', 'term']
        ordering = ['-year', '-term']
    
    def __str__(self):
        return f"{self.learner} - Year {self.year} Term {self.term}"
