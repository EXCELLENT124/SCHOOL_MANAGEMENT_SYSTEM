import io
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


def teacher_required(view_func):
    """Decorator to require teacher login."""
    def wrapper(request, *args, **kwargs):
        teacher_id = request.session.get('teacher_id')
        if not teacher_id:
            return redirect('teacher_login')
        return view_func(request, *args, **kwargs)
    return wrapper
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db.models import Count, Avg
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from .models import (
    Grade, Application, Document, Learner, Exam, 
    Registration, FinancialInfo, Stream, ProgressReport, Teacher, Task, TaskSubmission,
    BursaryScholarshipRecord, ExamStatus
)
from .forms import (
    ApplicationForm, DocumentUploadForm, LearnerLoginForm,
    RegistrationForm, StudentEnquiryForm, CreatePINForm, CreateTeacherPINForm, SubmitMarksForm,
    TeacherLoginForm, TaskForm, TaskSubmissionForm, TaskGradingForm
)


def home(request):
    """Home page view."""
    grades = Grade.objects.filter(year=timezone.now().year)
    context = {
        'grades': grades,
        'total_learners': Learner.objects.filter(admission_status='registered').count(),
    }
    return render(request, 'portal/home.html', context)


def home_login(request):
    """Combined login handler for both learners and teachers."""
    if request.method == 'POST':
        login_type = request.POST.get('login_type', 'learner')
        
        if login_type == 'teacher':
            # Teacher login
            teacher_id = request.POST.get('teacher_id', '').strip().upper()
            pin = request.POST.get('teacher_pin', '')
            
            if teacher_id and pin:
                try:
                    teacher = Teacher.objects.get(teacher_id=teacher_id, pin=pin, is_active=True)
                    request.session['teacher_id'] = teacher.id
                    request.session['teacher_name'] = teacher.full_name
                    request.session['is_teacher'] = True
                    messages.success(request, f'Welcome back, {teacher.full_name}!')
                    return redirect('teacher_dashboard')
                except Teacher.DoesNotExist:
                    messages.error(request, 'Invalid Teacher ID or PIN.')
            else:
                messages.error(request, 'Please provide both Teacher ID and PIN.')
                
        else:
            # Learner login
            study_number = request.POST.get('study_number', '').strip().upper()
            pin = request.POST.get('pin', '')
            
            print(f"DEBUG: Learner login attempt - Study Number: '{study_number}', PIN: '{pin}'")  # Debug line
            
            if study_number and pin:
                try:
                    learner = Learner.objects.get(study_number=study_number, pin=pin)
                    print(f"DEBUG: Learner found: {learner.first_name} {learner.last_name}")  # Debug line
                    request.session['learner_id'] = learner.id
                    request.session['is_learner'] = True
                    messages.success(request, f'Welcome, {learner.first_name}!')
                    print(f"DEBUG: Redirecting to learner_dashboard")  # Debug line
                    return redirect('learner_dashboard')
                except Learner.DoesNotExist:
                    print(f"DEBUG: Learner not found for study_number: {study_number}")  # Debug line
                    messages.error(request, 'Invalid Study Number or PIN.')
            else:
                print(f"DEBUG: Missing study_number or pin")  # Debug line
                messages.error(request, 'Please provide both Study Number and PIN.')
    
    return redirect('home')


def admission_status_check(request):
    """Check admission status by application ID."""
    application = None
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        try:
            application = Application.objects.get(application_id=application_id.upper().strip())
        except Application.DoesNotExist:
            messages.error(request, 'Application not found. Please check your Application ID.')
    
    return render(request, 'portal/admission_status.html', {'application': application})


def available_spaces(request):
    """View available spaces per grade."""
    grades = Grade.objects.filter(year=timezone.now().year).order_by('grade_number')
    return render(request, 'portal/available_spaces.html', {'grades': grades})


def apply_admission(request):
    """Admission application form."""
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(
                request, 
                f'Application submitted successfully! Your Application ID is: {application.application_id}. '
                f'Please save this ID to check your admission status.'
            )
            return redirect('upload_documents', application_id=application.application_id)
    else:
        form = ApplicationForm()
    
    return render(request, 'portal/apply_admission.html', {'form': form})


def upload_documents(request, application_id):
    """Upload required documents for application."""
    application = get_object_or_404(Application, application_id=application_id)
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.application = application
            document.save()
            messages.success(request, f'{document.get_document_type_display()} uploaded successfully!')
            
            # Check if all required documents are uploaded
            uploaded_types = application.documents.values_list('document_type', flat=True)
            if 'birth_certificate' in uploaded_types and 'previous_report' in uploaded_types:
                messages.success(request, 'All required documents have been uploaded!')
                return redirect('admission_status_check')
    else:
        form = DocumentUploadForm()
    
    uploaded_documents = application.documents.all()
    return render(request, 'portal/upload_documents.html', {
        'form': form,
        'application': application,
        'uploaded_documents': uploaded_documents
    })


def home_login(request):
    """Handle login from home page for both learners and teachers."""
    if request.method == 'POST':
        login_type = request.POST.get('login_type')
        
        if login_type == 'teacher':
            # Handle teacher login
            teacher_id = request.POST.get('teacher_id')
            pin = request.POST.get('teacher_pin')
            
            if teacher_id and pin:
                try:
                    teacher = Teacher.objects.get(teacher_id=teacher_id.upper().strip())
                    
                    if teacher.pin == pin and teacher.is_active:
                        request.session['teacher_id'] = teacher.id
                        request.session['is_teacher'] = True
                        messages.success(request, f'Welcome, {teacher.first_name}!')
                        return redirect('teacher_dashboard')
                    else:
                        messages.error(request, 'Incorrect PIN or teacher account is inactive.')
                        
                except Teacher.DoesNotExist:
                    messages.error(request, 'Teacher ID not found.')
            else:
                messages.error(request, 'Please provide both Teacher ID and PIN.')
                
        elif login_type == 'learner':
            # Handle learner login with detailed error handling
            study_number = request.POST.get('study_number')
            pin = request.POST.get('pin')

            if study_number and pin:
                study_number = study_number.upper().strip()
                try:
                    learner = Learner.objects.get(study_number=study_number)

                    if learner.pin == pin:
                        request.session['learner_id'] = learner.id
                        request.session['is_learner'] = True
                        messages.success(request, f'Welcome, {learner.first_name}!')
                        return redirect('learner_dashboard')
                    else:
                        messages.error(request, 'Incorrect PIN. Please try again.')

                except Learner.DoesNotExist:
                    # Check if there's an accepted application that hasn't created a learner profile yet
                    try:
                        application = Application.objects.get(study_number=study_number, status='accepted')
                        messages.warning(
                            request,
                            f'Study Number {study_number} exists but no PIN has been created yet. '
                            'Please create your PIN first.'
                        )
                        return redirect(f"{reverse('create_pin')}?application_id={application.application_id}")
                    except Application.DoesNotExist:
                        messages.error(
                            request,
                            f'Study Number {study_number} not found. Please check your Study Number or contact the school administration.'
                        )
            else:
                messages.error(request, 'Please provide both Study Number and PIN.')
        else:
            messages.error(request, 'Invalid login type.')
    
    # If not POST or login failed, redirect back to home
    return redirect('home')


def learner_login(request):
    """Learner login using study number and PIN."""
    if request.method == 'POST':
        form = LearnerLoginForm(request.POST)
        if form.is_valid():
            study_number = form.cleaned_data['study_number'].upper().strip()
            pin = form.cleaned_data['pin']
            
            # First, check if learner exists with this study number
            try:
                learner = Learner.objects.get(study_number=study_number)
                
                # Check if PIN matches
                if learner.pin == pin:
                    # Successful login
                    request.session['learner_id'] = learner.id
                    request.session['is_learner'] = True
                    
                    # Check if this is an AJAX request
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Welcome, {learner.first_name}!',
                            'redirect_url': reverse('learner_dashboard')
                        })
                    else:
                        messages.success(request, f'Welcome, {learner.first_name}!')
                        return redirect('learner_dashboard')
                else:
                    # Learner exists but PIN doesn't match
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': 'Incorrect PIN. Please try again.'
                        })
                    else:
                        messages.error(request, 'Incorrect PIN. Please try again.')
                    
            except Learner.DoesNotExist:
                # Learner with this study number doesn't exist
                # Check if there's an accepted application that hasn't created a learner profile yet
                try:
                    application = Application.objects.get(study_number=study_number, status='accepted')
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': f'Study Number {study_number} exists but no PIN has been created yet. Please create your PIN first.',
                            'redirect_url': f"{reverse('create_pin')}?application_id={application.application_id}"
                        })
                    else:
                        messages.warning(
                            request, 
                            f'Study Number {study_number} exists but no PIN has been created yet. '
                            'Please create your PIN first.'
                        )
                        return redirect(f"{reverse('create_pin')}?application_id={application.application_id}")
                except Application.DoesNotExist:
                    # No application found with this study number
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': f'Study Number {study_number} not found. Please check your Study Number or contact the school administration.'
                        })
                    else:
                        messages.error(
                            request, 
                            f'Study Number {study_number} not found. Please check your Study Number or contact the school administration.'
                        )
        else:
            # Form is invalid
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Please fill in all required fields correctly.'
                })
    else:
        form = LearnerLoginForm()
    
    return render(request, 'portal/learner_login.html', {'form': form})


def learner_logout(request):
    """Logout learner."""
    if 'learner_id' in request.session:
        del request.session['learner_id']
        del request.session['is_learner']
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def create_pin(request):
    """Allow applicants to create their PIN after application is accepted."""
    if request.method == 'POST':
        form = CreatePINForm(request.POST)
        if form.is_valid():
            application_id = form.cleaned_data['application_id']
            pin = form.cleaned_data['pin']
            
            try:
                application = Application.objects.get(application_id=application_id)
                
                # Check if application is accepted
                if application.status != 'accepted':
                    messages.error(
                        request, 
                        f'Your application status is: {application.get_status_display()}. '
                        'PIN creation is only available for accepted applications.'
                    )
                    return render(request, 'portal/create_pin.html', {'form': form})
                
                # Check if study number exists
                if not application.study_number:
                    messages.error(
                        request, 
                        'Study number not yet generated. Please wait for admin approval or contact the school.'
                    )
                    return render(request, 'portal/create_pin.html', {'form': form})
                
                # Create or update learner profile
                learner, created = Learner.objects.get_or_create(
                    study_number=application.study_number,
                    defaults={
                        'pin': pin,
                        'first_name': application.learner_name.split()[0] if application.learner_name else '',
                        'last_name': ' '.join(application.learner_name.split()[1:]) if len(application.learner_name.split()) > 1 else '',
                        'date_of_birth': application.date_of_birth,
                        'gender': application.gender,
                        'grade': application.grade_applying,
                        'admission_status': 'admitted',
                        'parent_name': application.parent_name,
                        'parent_email': application.parent_email,
                        'parent_phone': application.parent_phone,
                        'address': application.parent_address,
                        'application': application
                    }
                )
                
                if not created:
                    # Update PIN if learner already exists
                    learner.pin = pin
                    learner.save()
                else:
                    # Decrease available spaces for the grade when new learner is registered
                    grade = application.grade_applying
                    if grade.available_spaces > 0:
                        grade.available_spaces -= 1
                        grade.save()
                
                messages.success(
                    request, 
                    f'PIN created successfully! Your Study Number is: {application.study_number}. '
                    'You can now login using your Study Number and PIN.'
                )
                return redirect('learner_login')
                
            except Application.DoesNotExist:
                messages.error(request, 'Application not found.')
    else:
        # Pre-fill application ID if provided in GET params
        initial = {}
        if 'application_id' in request.GET:
            initial['application_id'] = request.GET.get('application_id')
        form = CreatePINForm(initial=initial)
    
    return render(request, 'portal/create_pin.html', {'form': form})


def create_teacher_pin(request):
    """Allow teachers to create their PIN."""
    if request.method == 'POST':
        form = CreateTeacherPINForm(request.POST)
        if form.is_valid():
            teacher_id = form.cleaned_data['teacher_id']
            pin = form.cleaned_data['pin']
            
            try:
                teacher = Teacher.objects.get(teacher_id=teacher_id)
                
                # Update teacher PIN
                teacher.pin = pin
                teacher.save()
                
                messages.success(
                    request, 
                    f'PIN created successfully! Your Teacher ID is: {teacher_id}. '
                    'You can now login using your Teacher ID and PIN.'
                )
                return redirect('teacher_login')
                
            except Teacher.DoesNotExist:
                messages.error(request, 'Teacher not found.')
    else:
        form = CreateTeacherPINForm()
    
    return render(request, 'portal/create_teacher_pin.html', {'form': form})





def teacher_required(view_func):
    """Decorator to check if teacher is logged in."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_teacher') or not request.session.get('teacher_id'):
            messages.error(request, 'Please login to access this page.')
            return redirect('teacher_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard with assigned classes and subjects."""
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    # Get teacher's assigned grades and subjects
    assigned_grades = teacher.grades.all()
    assigned_subjects = teacher.subjects.all()
    
    # Get learners in teacher's grades
    learners_in_grades = Learner.objects.filter(
        grade__in=assigned_grades,
        admission_status='registered'
    ).distinct()
    
    # Get recent exams submitted by this teacher
    recent_exams = Exam.objects.filter(teacher=teacher).order_by('-date_taken')[:10]
    
    # Create a structure showing subjects per grade
    grade_subjects = []
    for grade in assigned_grades:
        subjects_for_grade = assigned_subjects.filter(stream__grades=grade).distinct()
        grade_subjects.append({
            'grade': grade,
            'subjects': subjects_for_grade,
            'learner_count': learners_in_grades.filter(grade=grade).count()
        })
    
    context = {
        'teacher': teacher,
        'assigned_grades': assigned_grades,
        'assigned_subjects': assigned_subjects,
        'learners_count': learners_in_grades.count(),
        'recent_exams': recent_exams,
        'grade_subjects': grade_subjects,
    }
    return render(request, 'portal/teacher_dashboard.html', context)


@teacher_required
def submit_marks(request):
    """Allow teachers to submit learner marks."""
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    # Get grade filter from URL parameters
    grade_id = request.GET.get('grade')
    selected_grade = None
    if grade_id:
        try:
            selected_grade = Grade.objects.get(id=grade_id, teachers=teacher)
        except Grade.DoesNotExist:
            messages.warning(request, 'Invalid grade selected.')
    
    if request.method == 'POST':
        form = SubmitMarksForm(request.POST, teacher=teacher)
        if form.is_valid():
            exam = form.save(teacher=teacher)
            messages.success(
                request, 
                f'Marks submitted successfully for {exam.learner.full_name} - {exam.subject} ({exam.exam_type})'
            )
            return redirect('submit_marks')
    else:
        form = SubmitMarksForm(teacher=teacher)
    
    # Get recent submissions by this teacher
    recent_submissions = Exam.objects.filter(teacher=teacher).order_by('-date_taken')[:5]
    
    # Get available grades and subjects for filtering display
    available_grades = teacher.grades.all()
    
    context = {
        'teacher': teacher,
        'form': form,
        'recent_submissions': recent_submissions,
        'available_grades': available_grades,
        'selected_grade': selected_grade,
    }
    return render(request, 'portal/submit_marks.html', context)


def learner_required(view_func):
    """Decorator to check if learner is logged in."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_learner') or not request.session.get('learner_id'):
            messages.error(request, 'Please login to access this page.')
            return redirect('learner_login')
        return view_func(request, *args, **kwargs)
    return wrapper
    """Decorator to check if learner is logged in."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_learner') or not request.session.get('learner_id'):
            messages.error(request, 'Please login to access this page.')
            return redirect('learner_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@learner_required
def learner_dashboard(request):
    """Learner dashboard with profile information."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    # Get registration info
    try:
        registration = learner.registrations.latest('academic_year')
    except Registration.DoesNotExist:
        registration = None
    
    # Get or create financial info with defaults
    try:
        financial_info = learner.financial_info
    except FinancialInfo.DoesNotExist:
        financial_info = FinancialInfo.objects.create(
            learner=learner,
            tuition_fees=0,
            scholarship_status='none',
            scholarship_amount=0,
            bursary_status='none',
            bursary_amount=0,
            total_paid=0,
            balance_due=0,
            payment_status='unpaid'
        )
    
    # Get bursary and scholarship records
    funding_records = learner.funding_records.all()
    
    # Get recent exams
    recent_exams = learner.exams.all()[:5]
    
    # Get exam status for current year and term (for Recent Examinations section)
    from datetime import datetime
    current_year = datetime.now().year
    current_term = 2  # Term 2 as requested
    
    # Get learner's registered subjects
    learner_subjects = []
    latest_registration = learner.registrations.last()
    if latest_registration:
        subjects_str = latest_registration.subjects
        if subjects_str:
            learner_subjects = [s.strip() for s in subjects_str.split(',') if s.strip()]
    
    # Get exam status for current year and term
    exam_status_list = []
    for subject in learner_subjects:
        status_obj, created = ExamStatus.objects.get_or_create(
            learner=learner,
            subject=subject,
            academic_year=current_year,
            term=current_term,
            defaults={'status': 'na'}
        )
        
        # Check if learner actually wrote exam for this subject
        exam_exists = Exam.objects.filter(
            learner=learner,
            subject=subject,
            year=current_year,
            term=current_term
        ).exists()
        
        if exam_exists and status_obj.status == 'na':
            status_obj.status = 'yes'
            status_obj.save()
        
        exam_status_list.append({
            'subject': subject,
            'status': 'yes' if exam_exists else status_obj.status,
            'status_display': 'Yes' if exam_exists else status_obj.get_status_display()
        })
    
    context = {
        'learner': learner,
        'registration': registration,
        'financial_info': financial_info,
        'funding_records': funding_records,
        'recent_exams': recent_exams,
        'exam_status_list': exam_status_list,
        'current_year': current_year,
        'current_term': current_term,
    }
    return render(request, 'portal/learner_dashboard.html', context)


@learner_required
def academic_application(request):
    """View academic application process and status."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    application = None
    documents = []
    if learner.application:
        application = learner.application
        documents = application.documents.all()
    
    context = {
        'learner': learner,
        'application': application,
        'documents': documents,
    }
    return render(request, 'portal/academic_application.html', context)


@learner_required
def examinations(request):
    """View recent examinations with subject status for the learner."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    # Get current academic year and term
    from datetime import datetime
    current_year = datetime.now().year
    current_term = 2  # Set to Term 2 as requested
    
    # Get learner's registered subjects
    learner_subjects = []
    latest_registration = learner.registrations.last()
    if latest_registration:
        subjects_str = latest_registration.subjects
        if subjects_str:
            learner_subjects = [s.strip() for s in subjects_str.split(',') if s.strip()]
    
    # Get exam status for current year and term
    exam_status_list = []
    for subject in learner_subjects:
        status_obj, created = ExamStatus.objects.get_or_create(
            learner=learner,
            subject=subject,
            academic_year=current_year,
            term=current_term,
            defaults={'status': 'na'}
        )
        
        # Check if learner actually wrote exam for this subject
        exam_exists = Exam.objects.filter(
            learner=learner,
            subject=subject,
            year=current_year,
            term=current_term
        ).exists()
        
        if exam_exists and status_obj.status == 'no':
            status_obj.status = 'yes'
            status_obj.save()
        
        exam_status_list.append({
            'subject': subject,
            'status': 'yes' if exam_exists else status_obj.status,
            'status_display': 'Yes' if exam_exists else status_obj.get_status_display()
        })
    
    # Group exams by year and term (for historical data)
    exams = learner.exams.all()
    years = exams.values('year').distinct().order_by('-year')
    
    exam_data = {}
    for year in years:
        year_value = year['year']
        year_exams = exams.filter(year=year_value)
        terms = year_exams.values('term').distinct().order_by('term')
        
        exam_data[year_value] = {}
        for term in terms:
            term_value = term['term']
            term_exams = year_exams.filter(term=term_value)
            exam_data[year_value][term_value] = term_exams
    
    # Calculate overall statistics
    if exams.exists():
        overall_average = exams.aggregate(avg=Avg('marks'))['avg']
    else:
        overall_average = None
    
    context = {
        'learner': learner,
        'exam_status_list': exam_status_list,
        'current_year': current_year,
        'current_term': current_term,
        'exam_data': exam_data,
        'overall_average': overall_average,
        'total_exams': exams.count(),
    }
    return render(request, 'portal/examinations.html', context)


@learner_required
def examinations_pdf(request):
    """Generate PDF of examination status for the learner."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    # Get current academic year and term
    from datetime import datetime
    current_year = datetime.now().year
    current_term = 2  # Term 2 as requested
    
    # Get learner's registered subjects
    learner_subjects = []
    latest_registration = learner.registrations.last()
    if latest_registration:
        subjects_str = latest_registration.subjects
        if subjects_str:
            learner_subjects = [s.strip() for s in subjects_str.split(',') if s.strip()]
    
    # Get exam status for current year and term
    exam_status_list = []
    for subject in learner_subjects:
        status_obj, created = ExamStatus.objects.get_or_create(
            learner=learner,
            subject=subject,
            academic_year=current_year,
            term=current_term,
            defaults={'status': 'na'}
        )
        
        # Check if learner actually wrote exam for this subject
        exam_exists = Exam.objects.filter(
            learner=learner,
            subject=subject,
            year=current_year,
            term=current_term
        ).exists()
        
        if exam_exists and status_obj.status == 'na':
            status_obj.status = 'yes'
            status_obj.save()
        
        exam_status_list.append({
            'subject': subject,
            'status': 'yes' if exam_exists else status_obj.status,
            'status_display': 'Yes' if exam_exists else status_obj.get_status_display()
        })
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="examinations_{learner.study_number}_{current_year}_term{current_term}.pdf"'
    
    # Create PDF document
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Examination Status Report")
    
    # Learner info
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Name: {learner.full_name}")
    p.drawString(50, height - 100, f"Study Number: {learner.study_number}")
    p.drawString(50, height - 120, f"Academic Year: {current_year}")
    p.drawString(50, height - 140, f"Term: {current_term}")
    
    # Table headers
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 180, "Subject")
    p.drawString(300, height - 180, "Exam Status")
    
    # Draw line
    p.line(50, height - 190, 500, height - 190)
    
    # Table content
    p.setFont("Helvetica", 10)
    y_position = height - 210
    
    for subject_info in exam_status_list:
        if y_position < 50:  # Start new page if needed
            p.showPage()
            y_position = height - 50
            
        p.drawString(50, y_position, subject_info['subject'])
        p.drawString(300, y_position, subject_info['status_display'])
        y_position -= 20
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(50, 30, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    p.save()
    return response


@learner_required
def academic_registration(request):
    """Academic registration with rules, stream selection, and subject choices."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    # Check if learner is admitted
    can_register = learner.admission_status in ['admitted', 'registered']
    
    streams = Stream.objects.all()
    current_year = timezone.now().year
    
    # Get or create registration for current year
    try:
        registration = Registration.objects.get(learner=learner, academic_year=current_year)
    except Registration.DoesNotExist:
        registration = None

    # Get available subjects based on selected stream
    available_subjects = []
    selected_stream = None

    # Get financial info if it exists
    financial_info = None
    try:
        financial_info = learner.financial_info
    except FinancialInfo.DoesNotExist:
        financial_info = None

    if request.method == 'POST' and can_register:
        # Get stream from POST data
        stream_id = request.POST.get('stream')
        if stream_id:
            try:
                selected_stream = Stream.objects.get(id=stream_id)
                # Get subjects using the new get_subject_list method
                available_subjects = selected_stream.get_subject_list()
            except Stream.DoesNotExist:
                pass

        form = RegistrationForm(request.POST, instance=registration, available_subjects=available_subjects)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.learner = learner
            registration.academic_year = current_year

            if 'accept_rules' in request.POST:
                registration.rules_accepted = True
                registration.rules_accepted_date = timezone.now()

            registration.save()

            # Update learner stream
            if registration.stream:
                learner.stream = registration.stream
                learner.admission_status = 'registered'
                learner.save()

            # Save scholarship and bursary details to financial info
            financial_info, _ = FinancialInfo.objects.get_or_create(learner=learner)
            scholarship_choice = form.cleaned_data.get('scholarship_choice')
            bursary_choice = form.cleaned_data.get('bursary_choice')
            scholarship_name = form.cleaned_data.get('scholarship_name', '').strip()
            bursary_name = form.cleaned_data.get('bursary_name', '').strip()

            if scholarship_choice == 'yes':
                financial_info.scholarship_status = 'partial'
                financial_info.scholarship_details = scholarship_name
            else:
                financial_info.scholarship_status = 'none'
                financial_info.scholarship_amount = 0
                financial_info.scholarship_details = ''

            if bursary_choice == 'yes':
                financial_info.bursary_status = 'pending'
                financial_info.bursary_details = bursary_name
            else:
                financial_info.bursary_status = 'none'
                financial_info.bursary_amount = 0
                financial_info.bursary_details = ''

            financial_info.save()
            
            # Create Bursary/Scholarship Records if provided
            current_year = timezone.now().year
            
            if scholarship_choice == 'yes' and scholarship_name:
                BursaryScholarshipRecord.objects.get_or_create(
                    learner=learner,
                    record_type='scholarship',
                    year=current_year,
                    defaults={
                        'code': scholarship_name[:50],
                        'description': scholarship_name,
                        'status': 'active',
                        'amount_allocated': 0,
                        'amount_utilized': 0
                    }
                )
            
            if bursary_choice == 'yes' and bursary_name:
                BursaryScholarshipRecord.objects.get_or_create(
                    learner=learner,
                    record_type='bursary',
                    year=current_year,
                    defaults={
                        'code': bursary_name[:50],
                        'description': bursary_name,
                        'status': 'active',
                        'amount_allocated': 0,
                        'amount_utilized': 0
                    }
                )

            messages.success(request, 'Registration completed successfully! You have registered for: ' + registration.subjects)
            return redirect('academic_registration')
    else:
        # For GET request, check if stream is already selected
        if registration and registration.stream:
            selected_stream = registration.stream
            available_subjects = selected_stream.get_subject_list()
        elif request.GET.get('stream'):
            # Allow pre-selecting stream via GET parameter
            try:
                selected_stream = Stream.objects.get(id=request.GET.get('stream'))
                available_subjects = selected_stream.get_subject_list()
            except Stream.DoesNotExist:
                pass

        initial_data = {'stream': selected_stream.id if selected_stream else None}
        if financial_info:
            initial_data.update({
                'scholarship_choice': 'yes' if financial_info.scholarship_status != 'none' else 'no',
                'scholarship_name': financial_info.scholarship_details,
                'bursary_choice': 'yes' if financial_info.bursary_status != 'none' else 'no',
                'bursary_name': financial_info.bursary_details,
            })

        form = RegistrationForm(
            instance=registration,
            available_subjects=available_subjects,
            initial=initial_data
        )
    
    # Create a dictionary of stream subjects for JavaScript
    stream_subjects_data = {}
    for stream in streams:
        stream_subjects_data[stream.id] = stream.get_subject_list()
    
    context = {
        'learner': learner,
        'can_register': can_register,
        'streams': streams,
        'registration': registration,
        'form': form,
        'selected_stream': selected_stream,
        'available_subjects': available_subjects,
        'stream_subjects_json': JsonResponse(stream_subjects_data).content.decode('utf-8'),
    }
    return render(request, 'portal/academic_registration.html', context)


@learner_required
def download_proof_of_registration(request):
    """Generate and download proof of registration as PDF."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    current_year = timezone.now().year
    try:
        registration = Registration.objects.get(learner=learner, academic_year=current_year)
    except Registration.DoesNotExist:
        messages.error(request, 'No registration found for the current academic year.')
        return redirect('academic_registration')
    
    # Create PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, height - 2*cm, "SECONDARY SCHOOL")
    p.setFont("Helvetica", 12)
    p.drawCentredString(width/2, height - 2.8*cm, "Proof of Academic Registration")
    
    # Line separator
    p.line(2*cm, height - 3.5*cm, width - 2*cm, height - 3.5*cm)
    
    # Student Information
    y = height - 5*cm
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2*cm, y, "Student Information")
    p.setFont("Helvetica", 11)
    
    y -= 0.8*cm
    p.drawString(2*cm, y, f"Study Number: {learner.study_number}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Full Name: {learner.full_name()}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Grade: {learner.grade}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Stream: {registration.stream.name if registration.stream else 'Not assigned'}")
    
    # Registration Details
    y -= 1.2*cm
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2*cm, y, "Registration Details")
    p.setFont("Helvetica", 11)
    
    y -= 0.8*cm
    p.drawString(2*cm, y, f"Academic Year: {registration.academic_year}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Registration Date: {registration.registration_date.strftime('%B %d, %Y')}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Status: {registration.get_status_display()}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Rules Accepted: {'Yes' if registration.rules_accepted else 'No'}")
    
    # Fee Information
    try:
        financial_info = learner.financial_info
        y -= 1.2*cm
        p.setFont("Helvetica-Bold", 14)
        p.drawString(2*cm, y, "Fee Information")
        p.setFont("Helvetica", 11)
        
        y -= 0.8*cm
        p.drawString(2*cm, y, f"Tuition Fees: R{financial_info.tuition_fees}")
        y -= 0.6*cm
        p.drawString(2*cm, y, f"Registration Fee: R{registration.registration_fee}")
        y -= 0.6*cm
        p.drawString(2*cm, y, f"Payment Status: {financial_info.get_payment_status_display()}")
        
        if financial_info.scholarship_status != 'none':
            y -= 0.6*cm
            p.drawString(2*cm, y, f"Scholarship: {financial_info.get_scholarship_display()} (R{financial_info.scholarship_amount})")
        
        if financial_info.bursary_status != 'none':
            y -= 0.6*cm
            p.drawString(2*cm, y, f"Bursary: {financial_info.get_bursary_display()} (R{financial_info.bursary_amount})")
        
        y -= 0.6*cm
        p.drawString(2*cm, y, f"Balance Due: R{financial_info.balance_due}")
    except FinancialInfo.DoesNotExist:
        pass
    
    # Footer
    y = 3*cm
    p.line(2*cm, y + 0.5*cm, width - 2*cm, y + 0.5*cm)
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2, y, "This document serves as official proof of academic registration.")
    y -= 0.5*cm
    p.drawCentredString(width/2, y, f"Generated on {timezone.now().strftime('%B %d, %Y at %H:%M')}")
    
    # Official stamp area
    y = 6*cm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(width - 6*cm, y, "Official Stamp")
    p.rect(width - 6*cm, y - 2.5*cm, 4*cm, 2.5*cm)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    filename = f"proof_of_registration_{learner.study_number}_{current_year}.pdf"
    
    return FileResponse(buffer, as_attachment=True, filename=filename)


def generate_academic_timetable(subjects, learner):
    """Generate a weekly timetable with randomly assigned subjects."""
    import random
    random.seed(learner.study_number)  # Consistent schedule per learner
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    # Define periods: 1-2, Break, 3-4, Break, 5-7
    # Total teaching periods per day: 7 (excluding breaks)
    teaching_periods = list(range(7))  # 0-6 representing 7 teaching periods
    
    timetable = {day: [] for day in days}
    
    # Ensure each subject gets fair distribution across the week
    # We'll assign subjects randomly but try to spread them out
    subject_list = subjects * 3  # Repeat subjects to fill all slots
    random.shuffle(subject_list)
    
    slot_index = 0
    for day in days:
        day_schedule = []
        for period_num in range(9):  # Total 9 rows including breaks
            if period_num == 2:
                day_schedule.append({'type': 'break', 'name': 'Small Break (30 min)', 'time': '09:30 - 10:00'})
            elif period_num == 5:
                day_schedule.append({'type': 'break', 'name': 'Long Break (1 hour)', 'time': '12:00 - 13:00'})
            else:
                # Assign a subject to this teaching period
                if slot_index < len(subject_list):
                    subject = subject_list[slot_index]
                    slot_index += 1
                else:
                    # If we run out, reshuffle and continue
                    random.shuffle(subjects)
                    subject = subjects[0] if subjects else 'Study Period'
                
                # Calculate time based on period position
                if period_num == 0:
                    time_slot = '07:30 - 08:30'
                elif period_num == 1:
                    time_slot = '08:30 - 09:30'
                elif period_num == 3:
                    time_slot = '10:00 - 11:00'
                elif period_num == 4:
                    time_slot = '11:00 - 12:00'
                elif period_num == 6:
                    time_slot = '13:00 - 14:00'
                elif period_num == 7:
                    time_slot = '14:00 - 15:00'
                else:  # period_num == 8
                    time_slot = '15:00 - 15:30'
                
                day_schedule.append({
                    'type': 'subject',
                    'name': subject,
                    'time': time_slot,
                    'period': period_num + 1 if period_num < 2 else period_num if period_num < 5 else period_num - 1
                })
        timetable[day] = day_schedule
    
    return timetable


@learner_required
def student_enquiry(request):
    """Student enquiry page with all academic information."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    # Get application status
    application = learner.application
    
    # Get latest progress report
    try:
        latest_report = learner.progress_reports.latest('date_issued')
    except ProgressReport.DoesNotExist:
        latest_report = None
    
    # Get registration info
    try:
        current_year = timezone.now().year
        registration = Registration.objects.get(learner=learner, academic_year=current_year)
        registered_subjects = [s.strip() for s in registration.subjects.split(',') if s.strip()]
    except Registration.DoesNotExist:
        registration = None
        registered_subjects = []

    # Build comprehensive progress report data with all terms
    progress_report_data = []
    for subject in registered_subjects:
        subject_terms = []
        
        for term in range(1, 5):
            # Get exam for this subject and term
            exam = learner.exams.filter(
                subject=subject,
                year=current_year,
                term=term
            ).first()
            
            if exam:
                subject_terms.append({
                    'marks': exam.marks,
                    'grade': exam.grade,
                    'level': get_level_from_marks(exam.marks)
                })
            else:
                subject_terms.append({
                    'marks': None,
                    'grade': 'N/A',
                    'level': 'N/A'
                })
        
        progress_report_data.append({
            'subject': subject,
            'term1': subject_terms[0],
            'term2': subject_terms[1],
            'term3': subject_terms[2],
            'term4': subject_terms[3]
        })
    
    # Calculate term averages as a list for easy template access
    term_averages_list = []
    for term in range(1, 5):
        term_marks = []
        for subject_data in progress_report_data:
            term_key = f'term{term}'
            if subject_data[term_key]['marks']:
                term_marks.append(float(subject_data[term_key]['marks']))
        
        if term_marks:
            avg = sum(term_marks) / len(term_marks)
            term_averages_list.append({
                'average': avg,
                'grade': calculate_grade_from_marks(avg),
                'level': get_level_from_marks(avg)
            })
        else:
            term_averages_list.append({'average': None, 'grade': 'N/A', 'level': 'N/A'})

    # Get uploaded documents (if any learner documents exist)
    learner_documents = []
    if application:
        learner_documents = application.documents.all()
    
    context = {
        'learner': learner,
        'application': application,
        'latest_report': latest_report,
        'registration': registration,
        'documents': learner_documents,
        'progress_report_data': progress_report_data,
        'term_averages_list': term_averages_list,
        'current_year': current_year,
    }
    
    # Generate Academic Timetable
    if registration and registered_subjects:
        timetable = generate_academic_timetable(registered_subjects, learner)
        context['timetable'] = timetable
        context['days'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        context['time_slots'] = [
            '07:30 - 08:30', '08:30 - 09:30',  # Periods 1-2
            '09:30 - 10:00',  # Small Break (30 min)
            '10:00 - 11:00', '11:00 - 12:00',  # Periods 3-4
            '12:00 - 13:00',  # Long Break (1 hour)
            '13:00 - 14:00', '14:00 - 15:00', '15:00 - 15:30'  # Periods 5-7 (last 30 min)
        ]
    
    return render(request, 'portal/student_enquiry.html', context)


@learner_required
def view_certificate(request, document_id):
    """View a specific uploaded certificate/document."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    document = get_object_or_404(Document, id=document_id)
    
    # Ensure the document belongs to the learner
    if document.application != learner.application:
        messages.error(request, 'You do not have permission to view this document.')
        return redirect('student_enquiry')
    
    return FileResponse(document.file)


@learner_required
def progress_report_pdf(request):
    """Generate comprehensive progress report PDF with all terms."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    # Get current year
    current_year = timezone.now().year
    
    # Get registration info
    try:
        registration = Registration.objects.get(learner=learner, academic_year=current_year)
        registered_subjects = [s.strip() for s in registration.subjects.split(',') if s.strip()]
    except Registration.DoesNotExist:
        registered_subjects = []
    
    # Build comprehensive marks data structure for PDF
    progress_report_data = []
    for subject in registered_subjects:
        subject_terms = []
        
        for term in range(1, 5):
            # Get exam for this subject and term
            exam = learner.exams.filter(
                subject=subject,
                year=current_year,
                term=term
            ).first()
            
            if exam:
                subject_terms.append({
                    'marks': exam.marks,
                    'grade': exam.grade,
                    'level': get_level_from_marks(exam.marks)
                })
            else:
                subject_terms.append({
                    'marks': None,
                    'grade': 'N/A',
                    'level': 'N/A'
                })
        
        progress_report_data.append({
            'subject': subject,
            'term1': subject_terms[0],
            'term2': subject_terms[1],
            'term3': subject_terms[2],
            'term4': subject_terms[3]
        })
    
    # Calculate term averages as a list
    term_averages_list = []
    for term in range(1, 5):
        term_marks = []
        term_key = f'term{term}'
        for subject_data in progress_report_data:
            if subject_data[term_key]['marks']:
                term_marks.append(float(subject_data[term_key]['marks']))
        
        if term_marks:
            avg = sum(term_marks) / len(term_marks)
            term_averages_list.append({
                'average': avg,
                'grade': calculate_grade_from_marks(avg),
                'level': get_level_from_marks(avg)
            })
        else:
            term_averages_list.append({'average': None, 'grade': 'N/A', 'level': 'N/A'})
    
    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Add School Logo at top center with perfect positioning
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        # Logo positioned at top center
        logo_width = 3*cm
        logo_height = 3*cm
        logo_x = (width - logo_width) / 2  # Center horizontally
        logo_y = height - 4*cm  # Position from top
        p.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
    
    # Header - positioned below logo
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 5*cm, "ACADEMIC PROGRESS REPORT")
    
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, height - 5.8*cm, "MAHASHE SECONDARY SCHOOL")
    
    # Student Information - positioned below header
    p.setFont("Helvetica", 11)
    y = height - 7*cm
    p.drawString(2*cm, y, f"Student Name: {learner.full_name()}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Study Number: {learner.study_number}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Grade: {learner.grade.grade_name if learner.grade else 'N/A'}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Year: {current_year}")
    y -= 0.6*cm
    p.drawString(2*cm, y, f"Date Generated: {timezone.now().strftime('%B %d, %Y')}")
    
    # Progress Report Table
    y -= 1.5*cm
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width/2, y, "ACADEMIC PERFORMANCE BY TERM")
    y -= 0.8*cm
    
    # Table headers
    p.setFont("Helvetica-Bold", 9)
    col_widths = [4*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm]
    col_starts = [2*cm]
    for i in range(len(col_widths) - 1):
        col_starts.append(col_starts[-1] + col_widths[i])
    
    # Header row
    headers = ['Subject', 'Term 1', 'Term 2', 'Term 3', 'Term 4']
    for i, header in enumerate(headers):
        p.drawString(col_starts[i], y, header)
    
    y -= 0.6*cm
    p.line(2*cm, y + 0.4*cm, width - 2*cm, y + 0.4*cm)
    
    # Data rows
    p.setFont("Helvetica", 8)
    for subject_data in progress_report_data:
        y -= 0.5*cm
        if y < 4*cm:  # New page if needed
            p.showPage()
            y = height - 2*cm
            p.setFont("Helvetica-Bold", 12)
            p.drawCentredString(width/2, y, "ACADEMIC PERFORMANCE (CONTINUED)")
            y -= 0.8*cm
            p.setFont("Helvetica-Bold", 9)
            for i, header in enumerate(headers):
                p.drawString(col_starts[i], y, header)
            y -= 0.6*cm
            p.line(2*cm, y + 0.4*cm, width - 2*cm, y + 0.4*cm)
            p.setFont("Helvetica", 8)
            y -= 0.5*cm
        
        # Subject name
        p.drawString(col_starts[0], y, subject_data['subject'][:25])
        
        # Term data using flattened keys
        term_keys = ['term1', 'term2', 'term3', 'term4']
        for idx, term_key in enumerate(term_keys):
            term_data = subject_data[term_key]
            if term_data['marks']:
                display_text = f"{term_data['marks']}% ({term_data['grade']}) L{term_data['level']}"
            else:
                display_text = "N/A"
            p.drawString(col_starts[idx + 1], y, display_text)
    
    # Term Averages row
    y -= 0.8*cm
    p.setFont("Helvetica-Bold", 9)
    p.drawString(col_starts[0], y, "TERM AVERAGE")
    for idx, avg_data in enumerate(term_averages_list):
        if avg_data['average']:
            display_text = f"{avg_data['average']:.1f}% ({avg_data['grade']}) L{avg_data['level']}"
        else:
            display_text = "N/A"
        p.drawString(col_starts[idx + 1], y, display_text)
    
    p.line(2*cm, y - 0.2*cm, width - 2*cm, y - 0.2*cm)
    
    # Legend
    y -= 1.5*cm
    if y < 5*cm:
        p.showPage()
        y = height - 3*cm
    
    p.setFont("Helvetica-Bold", 10)
    p.drawString(2*cm, y, "Grade Scale:")
    y -= 0.5*cm
    p.setFont("Helvetica", 9)
    p.drawString(2*cm, y, "A (80-100%) = Outstanding    B (70-79%) = Very Good    C (60-69%) = Good    D (50-59%) = Satisfactory")
    y -= 0.4*cm
    p.drawString(2*cm, y, "E (40-49%) = Pass    F (0-39%) = Fail")
    y -= 0.5*cm
    p.drawString(2*cm, y, "Level: 7=A, 6=B, 5=C, 4=D, 3=E, 2=F, 1=Fail")
    
    # Footer
    p.setFont("Helvetica-Oblique", 8)
    y = 2*cm
    p.drawCentredString(width/2, y, "This is a computer-generated progress report and does not require a signature.")
    y -= 0.4*cm
    p.drawCentredString(width/2, y, f"Generated on {timezone.now().strftime('%B %d, %Y at %H:%M')}")
    
    p.save()
    buffer.seek(0)
    
    response = FileResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Progress_Report_{learner.study_number}_{current_year}.pdf"'
    return response


def get_level_from_marks(marks):
    """Convert marks to level (1-7 scale)."""
    if marks >= 80:
        return 7
    elif marks >= 70:
        return 6
    elif marks >= 60:
        return 5
    elif marks >= 50:
        return 4
    elif marks >= 40:
        return 3
    elif marks >= 30:
        return 2
    else:
        return 1


def calculate_grade_from_marks(marks):
    """Calculate letter grade from marks."""
    if marks >= 80:
        return 'A'
    elif marks >= 70:
        return 'B'
    elif marks >= 60:
        return 'C'
    elif marks >= 50:
        return 'D'
    elif marks >= 40:
        return 'E'
    else:
        return 'F'


# Teacher Views
def teacher_login(request):
    """Teacher login view."""
    if request.method == 'POST':
        form = TeacherLoginForm(request.POST)
        if form.is_valid():
            teacher = form.cleaned_data['teacher']
            # Store teacher in session
            request.session['teacher_id'] = teacher.id
            request.session['teacher_name'] = teacher.full_name
            request.session['is_teacher'] = True
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Welcome back, {teacher.full_name}!',
                    'redirect_url': reverse('teacher_dashboard')
                })
            else:
                messages.success(request, f'Welcome back, {teacher.full_name}!')
                return redirect('teacher_dashboard')
        else:
            # Form is invalid
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid credentials. Please try again.'
                })
    else:
        form = TeacherLoginForm()
    
    return render(request, 'portal/teacher_login.html', {'form': form})


def teacher_logout(request):
    """Teacher logout view."""
    if 'teacher_id' in request.session:
        del request.session['teacher_id']
    if 'teacher_name' in request.session:
        del request.session['teacher_name']
    request.session['is_teacher'] = False
    messages.info(request, 'You have been logged out successfully.')
    return redirect('teacher_login')


@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard view."""
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    # Get teacher's tasks
    tasks = Task.objects.filter(teacher=teacher).order_by('-created_at')
    
    # Get statistics
    total_tasks = tasks.count()
    active_tasks = tasks.filter(is_active=True).count()
    total_submissions = TaskSubmission.objects.filter(task__teacher=teacher).count()
    
    context = {
        'teacher': teacher,
        'tasks': tasks[:5],  # Show recent 5 tasks
        'total_tasks': total_tasks,
        'active_tasks': active_tasks,
        'total_submissions': total_submissions,
    }
    return render(request, 'portal/teacher_dashboard.html', context)


@teacher_required
def create_task(request):
    """Create a new task."""
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            task = form.save(commit=False)
            task.teacher = teacher
            task.save()
            messages.success(request, f'Task "{task.title}" has been created successfully!')
            return redirect('teacher_dashboard')
    else:
        form = TaskForm(teacher=teacher)
    
    return render(request, 'portal/create_task.html', {'form': form, 'teacher': teacher})


@teacher_required
def edit_task(request, task_id):
    """Edit an existing task."""
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    task = get_object_or_404(Task, id=task_id, teacher=teacher)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, teacher=teacher, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" has been updated successfully!')
            return redirect('teacher_dashboard')
    else:
        form = TaskForm(teacher=teacher, instance=task)
    
    return render(request, 'portal/edit_task.html', {'form': form, 'task': task, 'teacher': teacher})


@teacher_required
def task_submissions(request, task_id):
    """View and grade task submissions."""
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    task = get_object_or_404(Task, id=task_id, teacher=teacher)
    
    submissions = task.submissions.all().order_by('-submitted_at')
    
    context = {
        'teacher': teacher,
        'task': task,
        'submissions': submissions,
    }
    return render(request, 'portal/task_submissions.html', context)


@teacher_required
def grade_submission(request, task_id, submission_id):
    """Grade a task submission."""
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    task = get_object_or_404(Task, id=task_id, teacher=teacher)
    submission = get_object_or_404(TaskSubmission, id=submission_id, task=task)
    
    if request.method == 'POST':
        form = TaskGradingForm(request.POST, instance=submission)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.graded_by = teacher
            graded_submission.save()
            messages.success(request, f'Submission graded successfully! Marks: {graded_submission.marks_obtained}/{task.total_marks}')
            return redirect('task_submissions', task_id=task.id)
    else:
        form = TaskGradingForm(instance=submission)
    
    context = {
        'teacher': teacher,
        'task': task,
        'submission': submission,
        'form': form,
    }
    return render(request, 'portal/grade_submission.html', context)


# Learner Views for Tasks
@learner_required
def learner_tasks(request):
    """View tasks assigned to the learner."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    # Get tasks for learner's grade and subjects
    learner_subjects = [s.strip() for s in learner.registration.subjects.split(',')]
    tasks = Task.objects.filter(
        grade=learner.grade,
        subject__name__in=learner_subjects,
        is_active=True
    ).order_by('due_date')
    
    # Add submission status
    for task in tasks:
        try:
            submission = TaskSubmission.objects.get(task=task, learner=learner)
            task.submission = submission
        except TaskSubmission.DoesNotExist:
            task.submission = None
    
    context = {
        'learner': learner,
        'tasks': tasks,
    }
    return render(request, 'portal/learner_tasks.html', context)


@learner_required
def submit_task(request, task_id):
    """Submit a task."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    task = get_object_or_404(Task, id=task_id)
    
    # Check if task is for learner's grade and subject
    learner_subjects = [s.strip() for s in learner.registration.subjects.split(',')]
    if task.grade != learner.grade or task.subject.name not in learner_subjects:
        messages.error(request, 'You are not authorized to submit this task.')
        return redirect('learner_tasks')
    
    # Check if already submitted
    try:
        existing_submission = TaskSubmission.objects.get(task=task, learner=learner)
        messages.info(request, 'You have already submitted this task.')
        return redirect('learner_tasks')
    except TaskSubmission.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = TaskSubmissionForm(request.POST, request.FILES, task=task)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.task = task
            submission.learner = learner
            submission.save()
            
            # Update status if late
            if submission.submitted_at > task.due_date:
                submission.status = 'late'
                submission.save()
            
            messages.success(request, 'Task submitted successfully!')
            return redirect('learner_tasks')
    else:
        form = TaskSubmissionForm(task=task)
    
    context = {
        'learner': learner,
        'task': task,
        'form': form,
    }
    return render(request, 'portal/submit_task.html', context)


def api_grade_spaces(request):
    """API endpoint to get available spaces per grade."""
    grades = Grade.objects.filter(year=timezone.now().year)
    data = []
    for grade in grades:
        data.append({
            'grade': grade.grade_name,
            'capacity': grade.capacity,
            'available': grade.available_spaces,
            'filled': grade.capacity - grade.available_spaces
        })
    return JsonResponse({'grades': data})
