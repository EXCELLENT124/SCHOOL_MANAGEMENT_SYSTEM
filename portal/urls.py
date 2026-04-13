from django.urls import path
from . import views

urlpatterns = [
    # Home and Public Pages
    path('', views.home, name='home'),
    path('admission-status/', views.admission_status_check, name='admission_status_check'),
    path('available-spaces/', views.available_spaces, name='available_spaces'),
    
    # Application Process
    path('apply/', views.apply_admission, name='apply_admission'),
    path('apply/upload/<str:application_id>/', views.upload_documents, name='upload_documents'),
    
    # Learner Authentication
    path('login/', views.learner_login, name='learner_login'),
    path('logout/', views.learner_logout, name='learner_logout'),
    path('create-pin/', views.create_pin, name='create_pin'),
    
    # Learner Dashboard and iEnabler
    path('dashboard/', views.learner_dashboard, name='learner_dashboard'),
    path('academic-application/', views.academic_application, name='academic_application'),
    path('examinations/', views.examinations, name='examinations'),
    path('academic-registration/', views.academic_registration, name='academic_registration'),
    path('download-proof-registration/', views.download_proof_of_registration, name='download_proof_registration'),
    path('student-enquiry/', views.student_enquiry, name='student_enquiry'),
    path('certificate/<int:document_id>/', views.view_certificate, name='view_certificate'),
    
    # API Endpoints
    path('api/grade-spaces/', views.api_grade_spaces, name='api_grade_spaces'),
]
