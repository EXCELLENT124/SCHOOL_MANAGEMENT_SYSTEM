import io
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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
    Registration, FinancialInfo, Stream, ProgressReport
)
from .forms import (
    ApplicationForm, DocumentUploadForm, LearnerLoginForm,
    RegistrationForm, StudentEnquiryForm, CreatePINForm
)


def home(request):
    """Home page view."""
    grades = Grade.objects.filter(year=timezone.now().year)
    context = {
        'grades': grades,
        'total_learners': Learner.objects.filter(admission_status='registered').count(),
    }
    return render(request, 'portal/home.html', context)


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
                    messages.success(request, f'Welcome, {learner.first_name}!')
                    return redirect('learner_dashboard')
                else:
                    # Learner exists but PIN doesn't match
                    messages.error(request, 'Incorrect PIN. Please try again.')
                    
            except Learner.DoesNotExist:
                # Learner with this study number doesn't exist
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
                    # No application found with this study number
                    messages.error(
                        request, 
                        f'Study Number {study_number} not found. Please check your Study Number or contact the school administration.'
                    )
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


def learner_required(view_func):
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
    
    # Get financial info
    try:
        financial_info = learner.financial_info
    except FinancialInfo.DoesNotExist:
        financial_info = None
    
    # Get recent exams
    recent_exams = learner.exams.all()[:5]
    
    context = {
        'learner': learner,
        'registration': registration,
        'financial_info': financial_info,
        'recent_exams': recent_exams,
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
    """View all examinations taken by the learner."""
    learner_id = request.session.get('learner_id')
    learner = get_object_or_404(Learner, id=learner_id)
    
    # Group exams by year and term
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
        'exam_data': exam_data,
        'overall_average': overall_average,
        'total_exams': exams.count(),
    }
    return render(request, 'portal/examinations.html', context)


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
        
        form = RegistrationForm(
            instance=registration, 
            available_subjects=available_subjects,
            initial={'stream': selected_stream.id if selected_stream else None}
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
        p.drawString(2*cm, y, f"Tuition Fees: ${financial_info.tuition_fees}")
        y -= 0.6*cm
        p.drawString(2*cm, y, f"Registration Fee: ${registration.registration_fee}")
        y -= 0.6*cm
        p.drawString(2*cm, y, f"Payment Status: {financial_info.get_payment_status_display()}")
        
        if financial_info.scholarship_status != 'none':
            y -= 0.6*cm
            p.drawString(2*cm, y, f"Scholarship: {financial_info.get_scholarship_display()} (${financial_info.scholarship_amount})")
        
        if financial_info.bursary_status != 'none':
            y -= 0.6*cm
            p.drawString(2*cm, y, f"Bursary: {financial_info.get_bursary_display()} (${financial_info.bursary_amount})")
        
        y -= 0.6*cm
        p.drawString(2*cm, y, f"Balance Due: ${financial_info.balance_due}")
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


@learner_required
def student_enquiry(request):
    """Student enquiry page for viewing academic records and documents."""
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
    except Registration.DoesNotExist:
        registration = None
    
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
    }
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
