from django.contrib.auth.models import User, auth
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.timezone import now, datetime, timedelta
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.db.models import Count, Q, Sum
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import (
    OTP, Student, Course, Book, Borrowing, Teacher, StudentAttendance, 
    TeacherAttendance, Principal, LeaveRequest, Parent, ExamGrade,
    SchoolClass, Timetable, Exam, Driver, DisciplinaryRecord, BusAssignment, 
    SchoolNews, Event, EventRegistration, EventResult, UserProfile, Payment, FeeType,Message
)
from .forms import (
    OTPForm, ProfilePhotoForm, LeaveRequestForm, TeacherAttendanceForm, 
    PaymentForm, MessageForm
)
from .utils import generate_weekly_timetable
import razorpay
import random
import json
from django.db import IntegrityError






def home_view(request):
    return render(request, 'home.html')

@login_required
def logout_view(request): 
    logout(request) 
    return redirect('users:login') 


def generate_otp():
    return str(random.randint(100000, 999999))


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not all([username, password]):
            messages.error(request, "Both username and password are required.")
            return render(request, 'users/login.html')

        user = authenticate(request, username=username, password=password)
        if user:
            otp_code = generate_otp()
            OTP.objects.update_or_create(
                user=user, defaults={'otp_code': otp_code, 'created_at': timezone.now()}
            )
            recipient = user.email
            subject="otp"
            message= f'your otp is: {otp_code}' 
            send_mail(subject,message,settings.EMAIL_HOST_USER,[recipient])
            
            request.session['otp_user_id'] = user.id
            return redirect('users:verify_otp')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'users/login.html')


def verify_otp(request):
    user_id = request.session.get('otp_user_id')

    if not user_id:
        return redirect('users:login')

    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "User not found.")
        return redirect('users:login')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            otp_record = OTP.objects.filter(user=user).first()
            if otp_record and otp_record.otp_code == otp and otp_record.is_valid():
                login(request, user)
                if user.is_staff:
                    return redirect('users:admin_dashboard')
                user_profile = UserProfile.objects.filter(user=user).first()
                if not user_profile:
                    messages.error(request, "User profile not found.")
                    return redirect('users:login')
                
                if user_profile.role == 'teacher':
                    return redirect('users:teacher_dashboard')
                elif user_profile.role == 'student':
                    return redirect('users:student_dashboard')
                # elif user_profile.role == 'admin':
                #     return redirect('users:admin_dashboard')
                elif user_profile.role == 'principal':
                    return redirect('users:principal_dashboard')
                elif user_profile.role == 'parent':
                    return redirect('users:parent_dashboard')
                else:
                    messages.error(request, "Role not recognized.")
                    return redirect('users:login')
            else:
                messages.error(request, "Invalid or expired OTP")
    else:
        form = OTPForm()
    return render(request, 'users/verify_otp.html', {'form': form})


def reset_password(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(str(user.pk).encode())
                domain = get_current_site(request).domain
                link = f"http://{domain}/users/reset-password-confirm/{uid}/{token}/"
                send_mail(
                    "Password Reset",
                    f"Click the link below to reset your password:\n{link}",
                    "naseehamuhammed3@example.com",
                    [user.email],
                )
                return render(request, 'users/reset_password_done.html')
            else:
                messages.error(request, "No user with that email address exists.")
    else:
        form = PasswordResetForm()

    return render(request, 'users/reset_password.html', {'form': form})


def enroll_student(request):
    school_classes = SchoolClass.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        dob = request.POST.get('dob')
        address = request.POST.get('address')
        grade = request.POST.get('grade') 
        hobbies=request.POST.get('hobbies') 
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not all([name, dob, email, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return render(request, 'users/enroll_student.html', {
                'name': name, 'dob': dob, 'address': address, 'grade': grade,
                'email': email, 'school_classes': school_classes,hobbies:'hobbies'
            })

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'users/enroll_student.html', {
                'name': name, 'dob': dob, 'address': address, 'grade': grade,
                'email': email, 'school_classes': school_classes,hobbies:'hobbies'
            })

        if User.objects.filter(username=name).exists():
            messages.error(request, "A user with this name already exists.")
            return render(request, 'users/enroll_student.html', {
                'school_classes': school_classes
            })

        try:
            
            user = User.objects.create_user(username=name, password=password, email=email)
            user_profile = UserProfile.objects.create(user=user, role='student')

            student = Student.objects.create(
                profile=user_profile,
                address=address,
                dob=dob,
                school_class_id=grade,
                hobbies=hobbies 
            )

            messages.success(request, "Student enrolled successfully.")
            return redirect('users:login')  

        except IntegrityError:
            messages.error(request, "An error occurred while enrolling the student. Please try again.")
            return render(request, 'users/enroll_student.html', {
                'school_classes': school_classes
            })

    return render(request, 'student/enroll_student.html', {'school_classes': school_classes})


def enroll_teacher(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        dob = request.POST.get('dob')
        address = request.POST.get('address')
        courses = request.POST.get('courses')  
        qualification = request.POST.get('qualification')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        course_objects = Course.objects.filter(id=courses)
        if not course_objects.exists():
            messages.error(request, "Selected courses are invalid.")
            return render(request, 'users/enroll_teacher.html', {
                'name': name, 'dob': dob, 'address': address, 'courses': Course.objects.all(),
                'qualification': qualification, 'email': email,
            })
        
        if not all([name, dob, email, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return render(request, 'users/enroll_teacher.html', {
                'name': name, 'dob': dob, 'address': address, 'courses': Course.objects.all(),
                'qualification': qualification, 'email': email,
            })

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'users/enroll_teacher.html', {
                'name': name, 'dob': dob, 'address': address, 'courses': Course.objects.all(),
                'qualification': qualification, 'email': email,
            })

        if User.objects.filter(username=name).exists():
            messages.error(request, "A user with this name already exists.")
            return render(request, 'users/enroll_teacher.html', {
                'name': name, 'dob': dob, 'address': address, 'courses': Course.objects.all(),
                'qualification': qualification, 'email': email,
            })

        try:
            user = User.objects.create_user(username=name, password=password, email=email)
            user_profile = UserProfile.objects.create(user=user, role='teacher')
            teacher = Teacher.objects.create(
                profile=user_profile,
                address=address,
                qualification=qualification,
                dob=dob,
                courses_id=courses
    
            )

            messages.success(request, "Teacher enrolled successfully.")
            return redirect('users:login')

        except IntegrityError:
            messages.error(request, "An error occurred while enrolling the teacher. Please try again.")
            return render(request, 'users/enroll_teacher.html', {
                'name': name, 'dob': dob, 'address': address, 'courses': Course.objects.all(),
                'qualification': qualification, 'email': email,
            })

    return render(request, 'teacher/enroll_teacher.html', {'courses': Course.objects.all()})


def enroll_principal(request):
    if request.method == 'POST':
        
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        resume = request.FILES.get('resume')

        if not all([name, contact, email, password, confirm_password, resume]):
            messages.error(request, "All fields are required, including the resume.")
            return render(request, 'users/enroll_principal.html', {
                'name': name, 'contact': contact, 'email': email
            })

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'users/enroll_principal.html', {
                'name': name, 'contact': contact, 'email': email
            })

        if User.objects.filter(email=email).exists() or Principal.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, 'users/enroll_principal.html', {
                'name': name, 'contact': contact, 'email': email
            })

        try:
            user = User.objects.create_user(username=name, password=password, email=email)
            user_profile = UserProfile.objects.create(user=user, role='principal')

            Principal.objects.create(
                profile=user_profile,
                name=name,
                contact=contact,
                email=email,
                resume=resume
            )

            messages.success(request, "Principal enrolled successfully.")
            return redirect('users:login')

        except IntegrityError:
            messages.error(request, "An error occurred. Please try again.")
            return render(request, 'principal/enroll_principal.html')

    return render(request, 'principal/enroll_principal.html')


def enroll_parent(request):
    students = Student.objects.all()

    if request.method == 'POST':
        parent_name = request.POST.get('parent_name')
        child_ids = request.POST.getlist('child')  
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        contact = request.POST.get('contact')

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('users:enroll_parent')

        if User.objects.filter(username=parent_name).exists():
            messages.error(request, "A user with this name already exists")
            return redirect('users:enroll_parent')
        
        if Parent.objects.filter(email=email).exists():
            messages.error(request, "A parent with this email already exists")
            return redirect('users:enroll_parent')
        
        user = User.objects.create_user(username=parent_name, password=password, email=email)
        user_profile = UserProfile.objects.create(user=user, role='parent')
        parent = Parent.objects.create(profile=user_profile, name=parent_name, email=email, contact=contact)

        for child_id in child_ids:
            try:
                child = Student.objects.get(id=child_id)
                parent.children.add(child)
            except Student.DoesNotExist:
                messages.error(request, f"The selected child with ID {child_id} does not exist")
                return redirect('users:enroll_parent')

        messages.success(request, "Parent successfully enrolled!")
        return redirect('users:login')

    return render(request, 'parent/enroll_parent.html', {'students': students})


@login_required
def admin_dashboard(request):
    user_count = User.objects.count()
    teacher_count = Teacher.objects.count()
    student_count = Student.objects.count()
    courses = Course.objects.all()

    context = {
        'user_count': user_count,
        'teacher_count': teacher_count,
        'student_count': student_count,
        'courses': courses,
    }
    return render(request, 'users/admin_dashboard.html', context)


@login_required
def principal_dashboard(request):
    if request.user.profile.is_principal:
        principal = Principal.objects.get(profile=request.user.profile)
        teachers = Teacher.objects.all()  
        students=Student.objects.all()
        return render(request, 'principal/principal_dashboard.html', {'teachers': teachers, 'principal': principal})
    else:
        return redirect('users:home')
    

@login_required
def teacher_dashboard(request, school_class_id=None):  
    teacher_profile = request.user.profile
    teacher = get_object_or_404(Teacher, profile=teacher_profile)
    
    if school_class_id:
        school_class = get_object_or_404(SchoolClass, id=school_class_id)
    else:
        school_class = None
    return render(request, 'teacher/teacher_dashboard.html', {'teacher': teacher, 'school_class': school_class})



@login_required
def student_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        student = Student.objects.get(profile=user_profile)
    except UserProfile.DoesNotExist:
        raise Http404("User profile not found")
    except Student.DoesNotExist:
        raise Http404("Student not found")

    if request.method == "POST":
        photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=student)
        if photo_form.is_valid():
            photo_form.save()
            return redirect('users:student_profile')  
    else:
        photo_form = ProfilePhotoForm(instance=student)

    context = {
        'student': student,
        'photo_form': photo_form,
    }

    return render(request, 'users/student_profile.html', context)
from django.http import JsonResponse


@login_required
def student_details(request):

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        parent = Parent.objects.get(profile=user_profile)
        
    except Parent.DoesNotExist:
        parent = None

    if parent:
        students = parent.children.all()
        student_data = [
            {
                'name': student.profile.user.username,
                'school_class':student.school_class.classname,
                'email': student.profile.user.email if student.profile else 'N/A',
                'address': student.address,
                  
            }
            
            for student in students
        ]
    else:
        student_data = None
    return render(request, 'parent/student_details.html', {'student_data': student_data})


@login_required
def mark_teacher_attendance(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        status = request.POST.get('status')
        teacher = request.user.profile.teacher
        TeacherAttendance.objects.create(teacher=teacher, date=date, status=status)
        return redirect('users:teacher_dashboard')  


@login_required
def view_teacher_attendance(request):
    date_filter = request.GET.get('date')
    if date_filter:
        attendance_records = TeacherAttendance.objects.filter(date=date_filter)
    else:
        attendance_records = TeacherAttendance.objects.all().order_by('-date')
    
    return render(request, 'users/teacher_attendance_list.html', {
        'attendance_records': attendance_records,
        'date_filter': date_filter,
    })

@login_required
def edit_teacher_attendance(request, attendance_id):
    attendance = get_object_or_404(TeacherAttendance, id=attendance_id)
    if request.method == 'POST':
        form = TeacherAttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect('users:view_teacher_attendance')
    else:
        form = TeacherAttendanceForm(instance=attendance)
    
    return render(request, 'users/edit_teacher_attendance.html', {'form': form})


@login_required
def request_leave(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            user_profile = get_object_or_404(UserProfile, user=request.user)
            teacher = get_object_or_404(Teacher, profile=user_profile)
            leave_request = form.save(commit=False)
            leave_request.teacher = teacher
            leave_request.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect('users:teacher_dashboard')
    else:
        form = LeaveRequestForm()

    return render(request, 'users/request_leave.html', {'form': form})

 
@login_required
def principal_dashboard(request):
    try:
        principal = Principal.objects.get(profile__user=request.user)
    except Principal.DoesNotExist:
        return redirect('users:home')

    teachers = Teacher.objects.all()
    leave_requests = LeaveRequest.objects.filter(status='Pending')

    return render(request, 'principal/principal_dashboard.html', {
        'principal': principal,
        'teachers': teachers,
        'leave_requests': leave_requests,
    })


@login_required
def approve_leave(request, leave_id):
    try:
        principal = Principal.objects.get(profile__user=request.user)
    except Principal.DoesNotExist:
        messages.error(request, "You do not have permission to approve leave requests.")
        return redirect('users:home')  

    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    leave_request.status = 'Approved'
    leave_request.save()

    messages.success(request, "Leave request approved successfully.")
    return redirect('users:principal_dashboard')


@login_required
def reject_leave(request, leave_id):
    try:
        principal = Principal.objects.get(profile__user=request.user)
    except Principal.DoesNotExist:
        messages.error(request, "You do not have permission to reject leave requests.")
        return redirect('users:home')  

    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    leave_request.status = 'Rejected'
    leave_request.save()
    messages.success(request, "Leave request rejected.")
    return redirect('users:principal_dashboard')

    
@login_required
def catalog(request):
    try:
        user_profile = request.user.profile 
    except UserProfile.DoesNotExist:
        raise Http404("User profile not found.")
    
    borrowed_books = None

    if user_profile.role == 'student' and hasattr(user_profile, 'student'):
        borrowed_books = Borrowing.objects.filter(
            student=user_profile.student,
            returned_date__isnull=True
        )
    elif user_profile.role == 'teacher' and hasattr(user_profile, 'teacher'):
        borrowed_books = Borrowing.objects.filter(
            teacher=user_profile.teacher,
            returned_date__isnull=True
        )

    books = Book.objects.all()
    return render(request, 'library/catalog.html', {
        'books': books, 
        'borrowed_books': borrowed_books
    })


@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if book.availability_status == 'Available':
        due_date = timezone.now().date() + timedelta(weeks=1)

        try:
            user_profile = request.user.profile  
        except UserProfile.DoesNotExist:
            raise Http404("User profile not found.")

        if user_profile.role == 'student' and hasattr(user_profile, 'student'):
            borrower = user_profile.student
        elif user_profile.role == 'teacher' and hasattr(user_profile, 'teacher'):
            borrower = user_profile.teacher
        else:
            raise Http404("User is neither a student nor a teacher.")

        if request.method == 'POST':
            borrowing = Borrowing.objects.create(
                book=book,
                student=borrower if user_profile.role == 'student' else None,
                teacher=borrower if user_profile.role == 'teacher' else None,
                due_date=due_date
            )
            book.availability_status = 'Checked Out'
            book.save()
            return redirect('users:catalog')
        return render(request, 'library/borrow_book.html', {'book': book})
    return render(request, 'library/catalog.html', {'message': 'This book is not available for borrowing.'})


@login_required
def return_book(request, borrowing_id):
    borrowing = get_object_or_404(Borrowing, id=borrowing_id)
    book = borrowing.book
    if borrowing.returned_date is None:
        borrowing.returned_date = timezone.now().date()
        if borrowing.is_overdue():
            overdue_days = (timezone.now().date() - borrowing.due_date).days
            if overdue_days > 0:
                borrowing.fine = overdue_days * 5 
                borrowing.save()
        book.availability_status = 'Available'
        book.save()
        return redirect('users:catalog')
    return render(request, 'library/catalog.html', {'message': 'This book is already returned.'})
 

@login_required
def manage_grades(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        exam_id = request.POST.get('exam_id')
        course_id = request.POST.get('course')
        school_class_id = request.POST.get('school_class')  
        marks = request.POST.get('marks')

        try:
            marks = int(marks)
            student = Student.objects.get(id=student_id)
            exam = Exam.objects.get(id=exam_id)
            course = Course.objects.get(id=course_id)
            school_class = SchoolClass.objects.get(id=school_class_id)  

            if exam.school_class != school_class:
                messages.error(request, 'This exam is not scheduled for the selected class.')
                return redirect('users:manage_grades')

            grade, created = ExamGrade.objects.update_or_create(
                student=student,
                exam=exam,
                course=course,
                defaults={'marks': marks}
            )

            messages.success(request, 'Grade saved successfully!')
        except ValueError:
            messages.error(request, 'Marks must be a valid integer.')
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
        except Exam.DoesNotExist:
            messages.error(request, 'Exam not found.')
        except Course.DoesNotExist:
            messages.error(request, 'Course not found.')
        except SchoolClass.DoesNotExist:
            messages.error(request, 'Class not found.')

        return redirect('users:manage_grades')  
    
    students = Student.objects.all()
    exams = Exam.objects.all()
    school_classes = SchoolClass.objects.all()  
    grades = ExamGrade.objects.all()
    teacher = request.user.profile.teacher  
    courses = Course.objects.filter(assigned_teachers=teacher)

    return render(request, 'teacher/manage_grades.html', {
        'students': students,
        'exams': exams,
        'courses': courses,
        'school_classes': school_classes, 
        'grades': grades,
    })


@staff_member_required
def generate_timetable_view(request):
    try:
        generate_weekly_timetable()
        return JsonResponse({'status': 'success', 'message': 'Timetable generated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    

@login_required
def student_timetable(request):
    student = Student.objects.get(profile=request.user.profile)
    timetable = Timetable.objects.filter(
        school_class=student.school_class,
        day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    ).order_by('day', 'time_slot')  
    context = {
        'student': student,
        'timetable': timetable,
    }
    return render(request, 'users/student_timetable.html', context)


@login_required
def student_dashboard(request):
    student = Student.objects.get(profile=request.user.profile)
    bus_assignment = BusAssignment.objects.filter(student=student).first()
    driver = None
    if bus_assignment and bus_assignment.bus.driver:

        driver = bus_assignment.bus.driver
    context = {
        'student': student,
        'bus_assignment': bus_assignment, 
        'driver':driver 
    }

    return render(request, 'student/student_dashboard.html', context)


@login_required
def parent_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        parent = Parent.objects.get(profile=user_profile)
    except UserProfile.DoesNotExist:
        raise Http404("User profile not found")
    except Parent.DoesNotExist:
        raise Http404("Parent not found")
    
    context = {
        'parent': parent,   
    }
    return render(request, 'parent/parent_profile.html', context)


@login_required
def parent_timetable(request):
    
    
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        parent = Parent.objects.get(profile=user_profile)
        
    except Parent.DoesNotExist:
        parent = None

    if parent:
        students = parent.children.all()

    timetables = {}
    for student in students:
        timetable = Timetable.objects.filter(
            school_class=student.school_class,
            day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        ).order_by('day', 'time_slot')
        timetables[student] = timetable

    context = {
        'parent': parent,
        'timetables': timetables,
    }
    return render(request, 'parent/parent_timetable.html', context)


@login_required
def parent_dashboard(request):

    user_profile = request.user.profile
    parent = get_object_or_404(Parent, profile=user_profile) 
    children = parent.children.all()
    teachers = Teacher.objects.all()
    pending_payments = Payment.objects.filter(
        student__in=children,
        status=Payment.PENDING
    )
    return render(request, 'parent/parent_dashboard.html', {
        'children': children,
        'pending_payments': pending_payments,
        'teachers': teachers,
       
    })
       

@login_required
def parent_invoices(request):

    parent = get_object_or_404(Parent, profile=request.user.profile)
    children = parent.children.all()
    fee_types = FeeType.objects.all()  

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            selected_fee_types = form.cleaned_data['fee_types']
            for student in children:
                for fee_type in selected_fee_types:
                    Payment.objects.create(
                        student=student,
                        fee_type=fee_type,
                        amount_paid=fee_type.amount,  
                    )
            messages.success(request, "Payment successfully processed for selected fee types.")
            return redirect('users:parent_invoices')  
    else:
        form = PaymentForm()

    return render(request, 'parent/parent_invoices.html', {
        'form': form,
        'children': children,
        'fee_types': fee_types,  
     })


def generate_bill(request):
    if request.method == 'POST':

        selected_fee_ids = request.POST.getlist('fee_types')
        selected_fees = FeeType.objects.filter(id__in=selected_fee_ids)
        parent = get_object_or_404(Parent, profile=request.user.profile)
        children = parent.children.all()  
        total_amount = sum(fee.amount for fee in selected_fees)
        total_amount_in_paise = int(total_amount * 100) 
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
        order = client.order.create({
            'amount': total_amount_in_paise,  
            'currency': 'INR',
            'payment_capture': '1',
        })
        for student in children:
            for fee in selected_fees:
                Payment.objects.create(
                    student=student,
                    fee_type=fee,
                    amount_paid=fee.amount,
                    status='pending',  
                )
        recipient = parent.profile.user.email
        subject = "Fee Payment Confirmation"
        message = f'Fee payment initiated successfully. Total Amount: {total_amount} INR.'

        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient])
        except Exception as e:
            print(f"Error sending email: {e}")

        context = {
            'parent': parent,
            'children': children,
            'selected_fees': selected_fees,
            'total_amount': total_amount,  
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,  
            'order_id': order['id'], 
        }
        return render(request, 'users/bill.html', context)


@login_required
def school_news(request):
    news = SchoolNews.objects.all().order_by('-created_at')
    context = {'news': news}
    return render(request, 'users/school_news.html', context)


@login_required
def message_inbox(request):
    user_profile = request.user.profile
    messages = Message.objects.filter(recipient=user_profile).order_by('-sent_at')
    return render(request, 'users/message_inbox.html', {'messages': messages})


@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user.profile
            message.save()
            return redirect('users:message_inbox')  
    else:
        form = MessageForm(user=request.user)
    return render(request, 'users/send_message.html', {'form': form})


@login_required
def view_message(request, id):
    message = get_object_or_404(Message, id=id)
    return render(request, 'users/view_message.html', {'message': message})


@login_required
def mark_attendance(request):
    school_classes = SchoolClass.objects.all()
    return render(request, 'users/mark_attendance.html', {'school_classes': school_classes})


@csrf_exempt
def get_students(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        school_class_id = request.POST.get('schoolclassid')
        if school_class_id:
            students = Student.objects.filter(school_class_id=school_class_id)
            student_data = [{'id': student.id, 'username': student.profile.user.username} for student in students]
            return JsonResponse({'students': student_data})
        else:
            return JsonResponse({'error': 'Invalid class ID'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def mark_student_attendance(request):
    students = Student.objects.all()  
    if request.method == 'POST':
        date = request.POST.get('date')
        status = request.POST.get('status')
        student_id = request.POST.get('student')
        student = Student.objects.get(id=student_id)
        StudentAttendance.objects.create(student=student, date=date, status=status)
        return redirect('users:teacher_dashboard') 

    return render(request, 'teacher/teacher_dashboard.html', {'students': students})

def events(request):
    events = Event.objects.all()
    return render(request, 'event/events.html', {'events': events})


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'event/event_detail.html', {'event': event})


def register_for_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        student_email = request.POST.get('student_email')

        EventRegistration.objects.create(
            event=event,
            student_name=student_name,
            student_email=student_email
        )

        recipient = student_email
        subject="event registration confirmation mail"
        message=f'You have successfully registered for {event.name}. A confirmation email has been sent to you.'
        send_mail(subject,message,settings.EMAIL_HOST_USER,[recipient])

        return render(request, 'event/registration_confirmation.html', {'event': event})
    
    return render(request, 'event/registerevent.html', {'event': event})


def event_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    results = EventResult.objects.filter(event=event)
    return render(request, 'event/event_results.html', {'event': event, 'results': results})


@login_required
def student_attendance(request):
    student = request.user.profile.student
    attendance_records = StudentAttendance.objects.filter(student=student).order_by('-date')
    current_month = timezone.now().month
    attendance_this_month = attendance_records.filter(date__month=current_month)

    return render(request, 'users/student_attendance.html', {
        'attendance_records': attendance_this_month,
    })


@login_required
def view_grades(request):
    student = request.user.profile.student  
    grades = ExamGrade.objects.filter(student=student).select_related('exam', 'course')
    return render(request, 'student/view_grades.html', {
        'grades': grades,
    })


@login_required
def view_grades_parent(request):
    if hasattr(request.user.profile, 'parent'):  
        parent = request.user.profile.parent
        children = parent.children.all() 

        grades = ExamGrade.objects.filter(student__in=children).select_related('exam', 'course')

        return render(request, 'parent/view_grades_parent.html', {
            'grades': grades,
            'parent': parent,
            'children': children,
        })
    return render(request, 'users/no_access.html')


@login_required
def view_report_card(request):
    student = request.user.profile.student  
    grades = ExamGrade.objects.filter(student=student).select_related('exam', 'course')
    attendance_data = StudentAttendance.objects.filter(student=student)
    total_classes = attendance_data.count()
    total_attendance = attendance_data.filter(status='present').count()
    
    remarks = "Needs Improvement"
    if total_attendance / total_classes >= 0.75:
        remarks = "Good Attendance"
    
    total_marks = sum([grade.marks for grade in grades])
    total_max_marks = len(grades) * 100  
    average_marks = (total_marks / total_max_marks) * 100 if total_max_marks else 0
    if average_marks >= 75:
        performance_remark = "Excellent Performance"
    elif 50 <= average_marks < 75:
        performance_remark = "Good Performance"
    else:
        performance_remark = "Needs Improvement"


    return render(request, 'users/view_report_card.html', {
        'student': student,
        'grades': grades,
        'attendance_data': attendance_data,
        'total_classes': total_classes,
        'total_attendance': total_attendance,
        'remarks': remarks,
        'performance_remark': performance_remark,
        'average_marks': average_marks
    })


@login_required
def view_report_card_parent(request, student_id=None):
    if request.user.profile.parent:
        parent = request.user.profile.parent
        
        if student_id:
            student = parent.children.filter(id=student_id).first()
            if not student:
                return redirect('error_page') 
        else:
            student = parent.children.first()
            if not student:
                return redirect('error_page')  
    else:
        try:
            student = request.user.profile.student
        except UserProfile.DoesNotExist:
            return redirect('error_page')  
    

    grades = ExamGrade.objects.filter(student=student).select_related('exam', 'course')
    
    attendance_data = StudentAttendance.objects.filter(student=student)
    total_classes = attendance_data.count()
    total_attendance = attendance_data.filter(status='Present').count()
    
    remarks = "Needs Improvement"
    if total_classes > 0 and total_attendance / total_classes >= 0.75:
        remarks = "Good Attendance"
    
    total_marks = sum([grade.marks for grade in grades])
    total_max_marks = len(grades) * 100  
    average_marks = (total_marks / total_max_marks) * 100 if total_max_marks else 0
    if average_marks >= 75:
        performance_remark = "Excellent Performance"
    elif 50 <= average_marks < 75:
        performance_remark = "Good Performance"
    else:
        performance_remark = "Needs Improvement"

    return render(request, 'users/view_report_card.html', {
        'student': student,
        'grades': grades,
        'attendance_data': attendance_data,
        'total_classes': total_classes,
        'total_attendance': total_attendance,
        'remarks': remarks,
        'performance_remark': performance_remark,
        'average_marks': average_marks,
        
    })


def is_principal(user):
    return user.profile.role == 'principal'

@login_required
@user_passes_test(is_principal)
def view_all_report_cards(request):
    students = Student.objects.all()
    report_cards = []

    for student in students:
        grades = ExamGrade.objects.filter(student=student).select_related('exam', 'course')
        attendance_data = StudentAttendance.objects.filter(student=student)
        total_classes = attendance_data.count()
        total_attendance = attendance_data.filter(status='present').count()

        attendance_remark = "Needs Improvement"
        if total_classes > 0 and total_attendance / total_classes >= 0.75:
            attendance_remark = "Good Attendance"

        total_marks = grades.aggregate(Sum('marks'))['marks__sum'] or 0
        total_max_marks = grades.count() * 100
        average_marks = (total_marks / total_max_marks) * 100 if total_max_marks > 0 else 0

        if average_marks >= 75:
            performance_remark = "Excellent Performance"
        elif 50 <= average_marks < 75:
            performance_remark = "Good Performance"
        else:
            performance_remark = "Needs Improvement"

        report_cards.append({
            'student': student,
            'grades': grades,
            'total_classes': total_classes,
            'total_attendance': total_attendance,
            'attendance_remark': attendance_remark,
            'average_marks': average_marks,
            'performance_remark': performance_remark,
        })

    return render(request, 'principal/view_all_report_cards.html', {
        'report_cards': report_cards,
    })


def attendance_reports(request):
    today = now().date()
    first_day_of_month = today.replace(day=1)
    
    daily_date = request.GET.get("daily_date")
    if daily_date:
        try:
            daily_date = datetime.strptime(daily_date, "%Y-%m-%d").date()
        except ValueError:
            daily_date = today  
    else:
        daily_date = today

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = first_day_of_month
    else:
        start_date = first_day_of_month

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            end_date = today
    else:
        end_date = today
   
    daily_report = StudentAttendance.objects.filter(date=daily_date).aggregate(
        total_present=Count('id', filter=Q(status='present')),
        total_absent=Count('id', filter=Q(status='absent')),
    )

    monthly_report = StudentAttendance.objects.filter(date__gte=start_date, date__lte=end_date).aggregate(
        total_present=Count('id', filter=Q(status='present')),
        total_absent=Count('id', filter=Q(status='absent')),
    )
    
    context = {
        'daily_report': daily_report,
        'monthly_report': monthly_report,
        'daily_date': daily_date,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'principal/attendance_reports.html', context)


def fee_payment_reports(request):
    today = now().date()
    first_day_of_month = today.replace(day=1)
    
    daily_date = request.GET.get("daily_date")
    if daily_date:
        try:
            daily_date = datetime.strptime(daily_date, "%Y-%m-%d").date()
        except ValueError:
            daily_date = today
    else:
        daily_date = today

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = first_day_of_month
    else:
        start_date = first_day_of_month

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            end_date = today
    else:
        end_date = today

    daily_report = Payment.objects.filter(payment_date=daily_date).aggregate(
        total_collected=Sum('amount_paid', filter=Q(status='completed')),
        total_pending=Sum('amount_paid', filter=Q(status='pending')),
    )
    
    monthly_report = Payment.objects.filter(payment_date__gte=start_date, payment_date__lte=end_date).aggregate(
        total_collected=Sum('amount_paid', filter=Q(status='completed')),
        total_pending=Sum('amount_paid', filter=Q(status='pending')),
    )
    
    context = {
        'daily_report': daily_report,
        'monthly_report': monthly_report,
        'daily_date': daily_date,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'principal/fee_payment_reports.html', context)


@login_required
def disciplinary_insights(request):
    records = DisciplinaryRecord.objects.all()
    total_records = records.count()
    severity_counts = records.values('severity').annotate(count=Count('severity'))
    
    severity_data = {
    'Low': severity_counts.get('Low', {}).get('count', 0),
    'Medium': severity_counts.get('Medium', {}).get('count', 0),
    'High': severity_counts.get('High', {}).get('count', 0),
}


    context = {
        'total_records': total_records,
        'severity_data': severity_data,
        'recent_records': records.order_by('-incident_date')[:5],
    }
    return render(request, 'principal_dashboard.html', context)

