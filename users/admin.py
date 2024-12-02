
from django.contrib import admin
from .models import (
    UserProfile, OTP, Course, SchoolClass, Teacher, Student, Parent, Principal,DisciplinaryRecord,
    Exam, ExamGrade, LeaveRequest, Book, Borrowing, StudentAttendance, TeacherAttendance,StudentTransferLog,
    FeeType, Discount, Payment, Invoice,Bus,BusAssignment,BusRoute,Driver,SchoolNews,Event,EventRegistration,EventResult
)

# Admin for UserProfile
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    search_fields = ('user__username', 'role')

# Admin for OTP
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'created_at', 'is_valid')
    search_fields = ('user__username', 'otp_code')

# Admin for Course
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# Admin for SchoolClass
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('classname',)
    search_fields = ('classname',)

# Admin for Teacher
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('profile', 'address', 'qualification', 'dob', 'contact')
    search_fields = ('profile__user__username', 'address', 'qualification')

# Admin for Student
class StudentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'school_class', 'dob')
    search_fields = ('profile__user__username', 'school_class__classname')

# Admin for Parent
class ParentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'contact')
    search_fields = ('name', 'email', 'contact')

# Admin for Principal
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ('profile', 'name', 'contact', 'email', 'qualification', 'joined_date')
    search_fields = ('name', 'contact', 'email')

class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'room', 'get_courses', 'exam_type', 'total_marks')
    search_fields = ('name', 'courses__name')

    # Add a custom method to display related courses
    def get_courses(self, obj):
        return ", ".join([course.name for course in obj.course.all()])
    get_courses.short_description = 'Courses'  # Column title in the admin panel


# Admin for ExamGrade
class ExamGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'course', 'marks', 'grade')
    search_fields = ('student__profile__user__username', 'exam__name')

# Admin for LeaveRequest
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'principal', 'reason', 'start_date', 'end_date', 'status', 'created_at')
    search_fields = ('teacher__profile__user__username', 'status')

# Admin for Book
class BookAdmin(admin.ModelAdmin):
    list_display = ('ISBN', 'title', 'author', 'genre', 'availability_status')
    search_fields = ('ISBN', 'title', 'author')

# Admin for Borrowing
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'teacher', 'borrow_date', 'due_date', 'returned_date', 'fine')
    search_fields = ('book__title', 'student__profile__user__username', 'teacher__profile__user__username')

# Admin for StudentAttendance
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status')
    search_fields = ('student__profile__user__username',)

# Admin for TeacherAttendance
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'date', 'status')
    search_fields = ('teacher__profile__user__username',)

# Admin for FeeType
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount')
    search_fields = ('name',)

# Admin for Discount
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('student_type', 'discount_percent')
    search_fields = ('student_type',)

# Admin for Payment
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_type', 'amount_paid', 'payment_date')
    search_fields = ('student__profile__user__username', 'fee_type__name')

# Admin for Invoice
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'total_amount', 'is_paid', 'invoice_date')
    search_fields = ('student__profile__user__username',)

from django.contrib import admin

@admin.register(StudentTransferLog)
class StudentTransferLogAdmin(admin.ModelAdmin):
    list_display = ['student', 'from_class', 'to_class', 'transfer_date', 'reason']
    list_filter = ['transfer_date', 'from_class', 'to_class']


# Registering the models with admin
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(OTP, OTPAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(SchoolClass, SchoolClassAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(Principal, PrincipalAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(ExamGrade, ExamGradeAdmin)
admin.site.register(LeaveRequest, LeaveRequestAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Borrowing, BorrowingAdmin)
admin.site.register(StudentAttendance, StudentAttendanceAdmin)
admin.site.register(TeacherAttendance, TeacherAttendanceAdmin)
admin.site.register(FeeType, FeeTypeAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(BusRoute)
admin.site.register(Bus)
admin.site.register(Driver)
admin.site.register(BusAssignment)

admin.site.register(SchoolNews)

admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(EventResult)
admin.site.register(DisciplinaryRecord)