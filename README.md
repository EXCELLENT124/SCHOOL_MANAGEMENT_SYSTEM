# Secondary School Management System

A comprehensive Django-based school management portal that allows parents to apply for admission, learners to view their profiles, and provides academic registration and enquiry capabilities.

## Features

### Parent Features:
- **Online Admission Application**: Fill out application forms with learner and parent details
- **Document Upload**: Upload required documents (Birth Certificate, Progress Report, etc.)
- **Check Admission Status**: Track application status using Application ID
- **View Available Spaces**: Check available spots per grade level

### Learner Features (iEnabler Portal):
- **Learner Login**: Secure login with Study Number and PIN
- **Profile Dashboard**: View personal information, grade, and stream
- **Registration Information**: View academic registration status and details
- **Financial Information**: View tuition fees, scholarship status, bursary status, and payment status
- **Academic Application**: View application process and uploaded documents
- **Examinations**: View all exam records with marks and grades
- **Academic Registration**: Accept rules, select stream, choose subjects (4-8 required), download proof of registration PDF
  - Stream-based subject selection with checkboxes
  - Real-time subject count validation
  - Science, Commercial, and General streams available
- **Student Enquiry**: View admission status, progress reports, certificates, and uploaded documents

### iEnabler Menu Categories:
1. **Academic Application** - View application process and status
2. **Examinations** - View all exams taken since joining
3. **Academic Registration** - Complete registration, choose stream, select subjects, download proof
4. **Student Enquiry** - View admission status, progress report, proof of registration, certificates

## Technology Stack

- **Backend**: Django 4.2+
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite (default), can be configured for PostgreSQL/MySQL
- **PDF Generation**: ReportLab
- **Icons**: Font Awesome 6

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or extract the project**:
   ```bash
   cd SCHOOLMANAGEMENTSYSTEM
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

7. **Load initial data** (optional - creates default grades and streams):
   ```bash
   python manage.py shell
   ```
   Then run:
   ```python
   from portal.models import Grade, Stream
   # Create grades
   for g in range(8, 13):
       Grade.objects.get_or_create(grade_number=g, grade_name=f'Grade {g}', defaults={'capacity': 30, 'year': 2024})
   # Create streams
   Stream.objects.get_or_create(code='science', defaults={'name': 'Science Stream', 'description': 'For students interested in science, technology, engineering, and mathematics', 'subjects': 'Mathematics, Physical Sciences, Life Sciences, Geography'})
   Stream.objects.get_or_create(code='commercial', defaults={'name': 'Commercial Stream', 'description': 'For students interested in business, economics, and accounting', 'subjects': 'Mathematics, Accounting, Business Studies, Economics'})
   Stream.objects.get_or_create(code='general', defaults={'name': 'General Stream', 'description': 'For students interested in arts, humanities, and general studies', 'subjects': 'History, Geography, Languages, Arts'})
   exit()
   ```

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

9. **Access the application**:
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage Guide

### For Parents:

1. **Apply for Admission**:
   - Click "Apply for Admission" on the home page
   - Fill in learner information, parent details, and emergency contact
   - Submit the application

2. **Upload Documents**:
   - After submitting the application, you'll be redirected to upload documents
   - Upload Birth Certificate and Previous Year Progress Report (required)
   - Optionally upload other documents

3. **Check Admission Status**:
   - Click "Check Status" in the navigation
   - Enter your Application ID (provided after submission)
   - View your application status

### For Learners:

1. **Login**:
   - Once accepted, you'll receive a Study Number and PIN via email
   - Click "Learner Login" and enter your credentials

2. **Access iEnabler Menu**:
   - Click the 3-line toggle button (top right) to open the iEnabler menu
   - Navigate between:
     - Dashboard (Profile, Registration, Financial Info)
     - Academic Application
     - Examinations
     - Academic Registration (accept rules, choose stream, download PDF)
     - Student Enquiry

3. **Complete Registration** (after admission):
   - Go to "Academic Registration"
   - Read and accept the rules and regulations
   - Choose your stream (Science, Commercial, or General)
   - Submit registration
   - Download Proof of Registration as PDF

### For Administrators:

1. **Access Admin Panel**:
   - Go to http://127.0.0.1:8000/admin/
   - Login with superuser credentials

2. **Manage Applications**:
   - Review applications under "Portal > Applications"
   - Update application status (pending, under_review, accepted, rejected)
   - Add review notes

3. **Create Learner Profiles**:
   - When accepting an application, manually create a Learner record with the study number
   - Set up FinancialInfo for tuition and scholarships

4. **Manage Grades**:
   - Add/modify grade capacities
   - Monitor available spaces

5. **Add Exam Records**:
   - Add examination results for learners
   - Create progress reports

## Project Structure

```
SCHOOLMANAGEMENTSYSTEM/
├── manage.py
├── requirements.txt
├── README.md
├── school_management/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── portal/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── templatetags/
│       ├── __init__.py
│       └── exam_tags.py
├── templates/
│   ├── base.html
│   └── portal/
│       ├── home.html
│       ├── apply_admission.html
│       ├── upload_documents.html
│       ├── admission_status.html
│       ├── available_spaces.html
│       ├── learner_login.html
│       ├── learner_dashboard.html
│       ├── academic_application.html
│       ├── examinations.html
│       ├── academic_registration.html
│       └── student_enquiry.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── media/
    └── (uploaded files)
```

## Security Notes

- Change the `SECRET_KEY` in `school_management/settings.py` for production
- Set `DEBUG = False` in production
- Configure proper email settings for sending Study Numbers and PINs
- Use HTTPS in production
- Regularly backup the database

## Customization

### Email Configuration
Add to `school_management/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

### Database Configuration
For PostgreSQL, update `DATABASES` in settings:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'school_db',
        'USER': 'db_user',
        'PASSWORD': 'db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Support

For issues or questions, please contact the school administration.

## License

This project is created for educational purposes.
