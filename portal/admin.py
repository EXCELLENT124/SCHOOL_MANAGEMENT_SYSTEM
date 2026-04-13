from django.contrib import admin
from .models import (
    Grade, Application, Document, Learner, 
    Exam, Registration, FinancialInfo, Stream, Subject
)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'stream_count', 'description_preview']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    list_editable = ['is_active']
    prepopulated_fields = {'code': ('name',)}
    
    fieldsets = (
        ('Subject Information', {
            'fields': ('name', 'code', 'description'),
            'description': 'Basic information about the subject'
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Inactive subjects will not be shown to applicants'
        }),
    )
    
    def stream_count(self, obj):
        count = obj.streams.count()
        return f"{count} stream(s)"
    stream_count.short_description = 'Used In'
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['grade_number', 'grade_name', 'capacity', 'available_spaces', 'year']
    list_filter = ['year', 'grade_number']
    search_fields = ['grade_name']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['application_id', 'learner_name', 'grade_applying', 'status', 'application_date', 'parent_email']
    list_filter = ['status', 'grade_applying', 'application_date']
    search_fields = ['learner_name', 'parent_email', 'application_id']
    readonly_fields = ['application_id', 'application_date', 'study_number']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['application', 'document_type', 'uploaded_at', 'verified']
    list_filter = ['document_type', 'verified', 'uploaded_at']

@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display = ['study_number', 'first_name', 'last_name', 'grade', 'date_of_birth', 'admission_status']
    list_filter = ['grade', 'admission_status', 'stream']
    search_fields = ['study_number', 'first_name', 'last_name', 'email']
    readonly_fields = ['study_number', 'pin']

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['learner', 'subject', 'exam_type', 'marks', 'grade', 'date_taken']
    list_filter = ['grade', 'exam_type', 'subject', 'date_taken']
    search_fields = ['learner__first_name', 'learner__last_name', 'subject']

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'subject_count', 'display_subjects', 'description_preview']
    list_filter = ['subjects']
    search_fields = ['name', 'code', 'description']
    filter_horizontal = ['subjects']
    prepopulated_fields = {'code': ('name',)}
    
    fieldsets = (
        ('Stream Information', {
            'fields': ('name', 'code', 'description'),
            'description': 'Basic information about the academic stream'
        }),
        ('Subjects', {
            'fields': ('subjects',),
            'description': 'Select subjects to include in this stream. Use the arrows to move subjects between available and chosen.'
        }),
        ('Legacy', {
            'fields': ('subjects_text',),
            'classes': ('collapse',),
            'description': 'Legacy text field for backward compatibility'
        }),
    )
    
    def subject_count(self, obj):
        count = obj.subjects.filter(is_active=True).count()
        return f"{count} subjects"
    subject_count.short_description = 'Active Subjects'
    
    def display_subjects(self, obj):
        subjects = obj.subjects.filter(is_active=True)[:5]
        subject_list = ', '.join([s.name for s in subjects])
        if obj.subjects.filter(is_active=True).count() > 5:
            subject_list += f" (+{obj.subjects.filter(is_active=True).count() - 5} more)"
        return subject_list or "No subjects assigned"
    display_subjects.short_description = 'Subjects'
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['learner', 'academic_year', 'stream', 'registration_date', 'status']
    list_filter = ['academic_year', 'stream', 'status', 'registration_date']
    search_fields = ['learner__study_number', 'learner__first_name', 'learner__last_name']

@admin.register(FinancialInfo)
class FinancialInfoAdmin(admin.ModelAdmin):
    list_display = ['learner', 'tuition_fees', 'scholarship_status', 'bursary_status', 'payment_status', 'total_paid']
    list_filter = ['scholarship_status', 'bursary_status', 'payment_status']
    search_fields = ['learner__study_number', 'learner__first_name', 'learner__last_name']
