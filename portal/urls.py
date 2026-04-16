from django.urls import path
from . import views

urlpatterns = [
    # Home and Public Pages
    path('', views.home, name='home'),
    path('home-login/', views.home_login, name='home_login'),
    path('admission-status/', views.admission_status_check, name='admission_status_check'),
    path('available-spaces/', views.available_spaces, name='available_spaces'),
    
    # Application Process
    path('apply/', views.apply_admission, name='apply_admission'),
    path('apply/upload/<str:application_id>/', views.upload_documents, name='upload_documents'),
    
    # Learner Authentication
    path('login/', views.learner_login, name='learner_login'),
    path('logout/', views.learner_logout, name='learner_logout'),
    path('create-pin/', views.create_pin, name='create_pin'),
    
    # Teacher Authentication
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    path('teacher/create-pin/', views.create_teacher_pin, name='create_teacher_pin'),
    
    # Teacher Dashboard and Features
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/submit-marks/', views.submit_marks, name='submit_marks'),
    
    # Task Management
    path('teacher/create-task/', views.create_task, name='create_task'),
    path('teacher/edit-task/<int:task_id>/', views.edit_task, name='edit_task'),
    path('teacher/task/<int:task_id>/submissions/', views.task_submissions, name='task_submissions'),
    path('teacher/task/<int:task_id>/grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    
    # Learner Dashboard and iEnabler
    path('dashboard/', views.learner_dashboard, name='learner_dashboard'),
    path('academic-application/', views.academic_application, name='academic_application'),
    path('examinations/', views.examinations, name='examinations'),
    path('academic-registration/', views.academic_registration, name='academic_registration'),
    path('download-proof-registration/', views.download_proof_of_registration, name='download_proof_registration'),
    path('student-enquiry/', views.student_enquiry, name='student_enquiry'),
    path('certificate/<int:document_id>/', views.view_certificate, name='view_certificate'),
    
    # Learner Tasks
    path('tasks/', views.learner_tasks, name='learner_tasks'),
    path('tasks/submit/<int:task_id>/', views.submit_task, name='submit_task'),
    
    # API Endpoints
    path('api/grade-spaces/', views.api_grade_spaces, name='api_grade_spaces'),
]
