from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from . import views

app_name = 'users'


urlpatterns = [
    path('',views.home_view,name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout_view'),
    path('verifyotp/',views.verify_otp, name='verify_otp'),
    path('studentenroll/', views.enroll_student, name='enroll_student'),
    path('stdprofile/', views.student_profile, name='student_profile'),
    path('teacherenroll/', views.enroll_teacher, name='enroll_teacher'),
    path('enrollprincipal/', views.enroll_principal, name='enroll_principal'),
    path('enrollparent/', views.enroll_parent, name='enroll_parent'),
    path('managegrades/', views.manage_grades, name='manage_grades'),
    path('resetpassword/',views.reset_password, name='reset_password'), 
    path('admindashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('principaldashboard/', views.principal_dashboard, name='principal_dashboard'),
    path('teacherdashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('studentdashboard/', views.student_dashboard, name='student_dashboard'),
    path('parentdashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('parentprofile/',views.parent_profile,name='parent_profile'),
    path('markteacherattendance/', views.mark_teacher_attendance, name='mark_teacher_attendance'),
    path('markstudentattendance/', views.mark_student_attendance, name='mark_student_attendance'),
    path('requestleave/', views.request_leave, name='request_leave'),
    path('catalog/', views.catalog, name='catalog'),
    path('borrow_book/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('return_book/<int:borrowing_id>/',views.return_book , name='return_book'),
    path('generatetimetable/', views.generate_timetable_view, name='generate_timetable'),
    path('studenttimetable/',views.student_timetable, name='student_timetable'),
    path('viewteacherattendance/', views.view_teacher_attendance, name='view_teacher_attendance'),
    path('attendance/edit/<int:attendance_id>/', views.edit_teacher_attendance, name='edit_teacher_attendance'),
    path('leave/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('leave/reject/<int:leave_id>/', views.reject_leave, name='reject_leave'),
    path('parenttimetable/', views.parent_timetable, name='parent_timetable'),
    path('studentdetails/',views.student_details,name='student_details'),
    path('parentinvoices/',views.parent_invoices, name='parent_invoices'),
    path('generate-bill/', views.generate_bill, name='generate_bill'),
    path('inbox/', views.message_inbox, name='message_inbox'),
    path('sendmessage', views.send_message, name='send_message'),
    path('view/<int:id>/', views.view_message, name='view_message'),
    path('schoolnews/', views.school_news, name='school_news'),
    path('attendance/', views.student_attendance, name='student_attendance'),
    path('mark_attendance/', views.mark_attendance, name='mark_attendance'),
    path('get_students/', views.get_students, name='get_students'), 
    path('student/view_grades/', views.view_grades, name='view_grades'),
    path('parents/viewgrades/',views.view_grades_parent,name='view_grades_parent'),
    path('events/', views.events, name='events'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/register/<int:event_id>/', views.register_for_event, name='registerevent'),
    path('events/results/<int:event_id>/', views.event_results, name='event_results'),
    path('view_report_card/', views.view_report_card, name='view_report_card'),
    path('view_report_card_parent/', views.view_report_card_parent, name='view_report_card_parent'),
    path('principal/report-cards/', views.view_all_report_cards, name='view_all_report_cards'),
    path('principal/attendance-report/', views.attendance_reports, name='attendance_report'),
    path('paymentreport/', views.fee_payment_reports, name='payment_report'),
   


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)