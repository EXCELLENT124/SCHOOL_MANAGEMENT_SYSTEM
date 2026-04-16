from django.contrib import admin
from .models import (
    Grade, Application, Document, Learner, 
    Exam, Registration, FinancialInfo, Stream, Subject, Teacher
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

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher_id', 'first_name', 'last_name', 'email', 'is_active', 'subject_count', 'grade_count', 'pin_status']
    list_filter = ['is_active', 'grades', 'subjects']
    search_fields = ['teacher_id', 'first_name', 'last_name', 'email', 'employee_number']
    readonly_fields = ['teacher_id', 'hire_date']
    filter_horizontal = ['grades', 'subjects']
    actions = ['generate_pins', 'reset_pins']
    
    fieldsets = (
        ('Teacher Information', {
            'fields': ('teacher_id', 'first_name', 'last_name', 'date_of_birth', 'gender'),
            'description': 'Basic teacher information'
        }),
        ('PIN Management', {
            'fields': ('pin',),
            'description': 'Teacher PIN for login (auto-generated)'
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address'),
            'description': 'Contact details for the teacher'
        }),
        ('Employment Information', {
            'fields': ('employee_number', 'hire_date', 'is_active'),
            'description': 'Employment and status information'
        }),
        ('Teaching Assignments', {
            'fields': ('grades', 'subjects'),
            'description': 'Grades and subjects this teacher is assigned to teach'
        }),
    )
    
    def subject_count(self, obj):
        return obj.subjects.count()
    subject_count.short_description = 'Subjects'
    
    def grade_count(self, obj):
        return obj.grades.count()
    grade_count.short_description = 'Grades'
    
    def pin_status(self, obj):
        """Display PIN status (masked for security)."""
        if obj.pin:
            return f"●●●●●● ({obj.pin})"
        return "Not set"
    pin_status.short_description = 'PIN'
    
    def generate_pins(self, request, queryset):
        """Generate PINs for selected teachers."""
        from .models import generate_teacher_pin
        
        updated = 0
        for teacher in queryset:
            if not teacher.pin:  # Only generate if no PIN exists
                teacher.pin = generate_teacher_pin()
                teacher.save()
                updated += 1
        
        if updated == 1:
            message = f"Generated PIN for 1 teacher."
        else:
            message = f"Generated PINs for {updated} teachers."
        
        self.message_user(request, message)
    generate_pins.short_description = "Generate PINs for selected teachers"
    
    def reset_pins(self, request, queryset):
        """Reset PINs for selected teachers."""
        from .models import generate_teacher_pin
        
        updated = 0
        for teacher in queryset:
            teacher.pin = generate_teacher_pin()
            teacher.save()
            updated += 1
        
        if updated == 1:
            message = f"Reset PIN for 1 teacher."
        else:
            message = f"Reset PINs for {updated} teachers."
        
        self.message_user(request, message)
    reset_pins.short_description = "Reset PINs for selected teachers"
    
    def response_change(self, request, obj):
        """Override to handle PIN regeneration."""
        if "_regenerate_pin" in request.POST:
            from .models import generate_teacher_pin
            obj.pin = generate_teacher_pin()
            obj.save()
            self.message_user(request, f"PIN regenerated for {obj.full_name}. New PIN: {obj.pin}")
            return self.response_post_save_change(request, obj)
        return super().response_change(request, obj)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change view to add PIN regeneration button."""
        extra_context = extra_context or {}
        extra_context['show_regenerate_pin'] = True
        return super().change_view(request, object_id, form_url, extra_context)
