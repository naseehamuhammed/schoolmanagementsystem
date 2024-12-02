from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('principal', 'Principal'),
    ('teacher', 'Teacher'),
    ('student', 'Student'),
    ('parent', 'Parent'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        expiry_time = self.created_at + timezone.timedelta(minutes=5)
        return timezone.now() < expiry_time
    
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

class Teacher(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    address = models.TextField(null=True, blank=True)
    qualification = models.CharField(max_length=200, null=True, blank=True)
    dob = models.DateField(default=timezone.now)
    contact = models.CharField(max_length=15, null=True, blank=True)
    resume = models.FileField(upload_to='teacher_resumes/', blank=True, null=True)
    courses = models.ForeignKey(Course,on_delete=models.CASCADE,related_name='assigned_teachers',null=True,blank=True)

class SchoolClass(models.Model):
    classname=models.CharField(max_length=10)   
    classteacher=models.ForeignKey(Teacher,on_delete=models.CASCADE,null=True,blank=True)

class FeeType(models.Model):
    CLASS_GROUP_CHOICES = [
        ('1-5' , 'Classes 1 to 5'),
        ('5-10', 'Classes 5 to 10'),
    ]
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    class_group = models.CharField(max_length=5, choices=CLASS_GROUP_CHOICES,null=True,blank=True)


class BusRoute(models.Model):
    route_name = models.CharField(max_length=100)
    start_point = models.CharField(max_length=100)
    end_point = models.CharField(max_length=100)
    stops = models.TextField(help_text="List the stops along the route", blank=True)


class Bus(models.Model):
    bus_number = models.CharField(max_length=20)
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE, related_name="buses")
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE)

class Student(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    address = models.TextField()
    school_class=models.ForeignKey(SchoolClass,on_delete=models.CASCADE,related_name='class_student',null=True,blank=True)  
    dob = models.DateField(default=timezone.now)
    photo = models.ImageField(upload_to="student_photos/", blank=True, null=True)
    course=models.ManyToManyField(Course,related_name='assigned_student')
    hobbies=models.TextField(null=True,blank = True)
    bus = models.ForeignKey('Bus', null=True, blank=True, on_delete=models.SET_NULL)

    def get_fee_for_class(self):
        if self.school_class:
            if self.school_class.classname in ['grade 1A', 'grade 2A', 'grade 3A', 'grade 4A', 'grade 5A']:
                return FeeType.objects.filter(class_group='1-5')
            elif self.school_class.classname in ['grade 6A', 'grade 7A', 'grade 8A', 'grade 9A', 'grade 10A']:
                return FeeType.objects.filter(class_group='5-10')
        return FeeType.objects.none()
    
    def transfer_to_class(self, new_class, reason=None):
        if self.school_class != new_class:
            StudentTransferLog.objects.create(
                student=self,
                from_class=self.school_class,
                to_class=new_class,
                reason=reason
            )
            self.school_class = new_class
            self.save()

class Parent(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    children = models.ManyToManyField(Student, related_name="parents") 
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    contact = models.CharField(max_length=15)


class Principal(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    qualification = models.CharField(max_length=200)
    resume = models.FileField(upload_to='principal_resumes/', blank=True, null=True)
    photo = models.ImageField(upload_to='principal_photos/', blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)
    message = models.TextField(blank=True, null=True)  

class StudentTransferLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transfer_logs')
    from_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_from')
    to_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_to')
    transfer_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(null=True, blank=True)

class Timetable(models.Model):
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    school_class = models.ForeignKey('SchoolClass', on_delete=models.CASCADE)
    day = models.CharField(max_length=20)  # E.g., Monday, Tuesday
    time_slot = models.TimeField() 
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='timetables',null=True,blank=True)


class Exam(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    room = models.CharField(max_length=50,null=True,blank=True)
    course = models.ManyToManyField(Course,related_name='exam_course' )
    exam_type = models.CharField(max_length=50, blank=True, null=True)
    total_marks = models.IntegerField(null=True, blank=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, blank=True, null=True, related_name='exams')


class ExamGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="grades")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    marks = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade = models.CharField(max_length=2, blank=True)  

    def save(self, *args, **kwargs):
        self.grade = self.calculate_grade(self.marks)
        super().save(*args, **kwargs)

    @staticmethod
    def calculate_grade(marks):
        if 40 <= marks <= 50:
            return "A"
        elif 35 <= marks < 40:
            return "B"
        elif 30 <= marks < 35:
            return "C"
        elif 25 <= marks < 30:
            return "D"
        else:
            return "F"
        

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    principal = models.ForeignKey(Principal, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Book(models.Model):
    ISBN = models.CharField(max_length=13, unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    genre = models.CharField(max_length=100)
    availability_status_choices = [
        ('Available', 'Available'),
        ('Checked Out', 'Checked Out'),
        ('Reserved', 'Reserved')
    ]
    availability_status = models.CharField(max_length=50, choices=availability_status_choices, default='Available')


class Borrowing(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.CASCADE)
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    fine = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def is_overdue(self):
        if self.returned_date is None and self.due_date < timezone.now().date():
            return True
        return False


class StudentAttendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()  
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Present')

    class Meta:
        unique_together = ('student', 'date')


class TeacherAttendance(models.Model):  
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date = models.DateField()  
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Present')


class Discount(models.Model):
    STUDENT_TYPE_CHOICES = [
        ('Scholarship', 'Scholarship'),
        ('Sibling', 'Sibling'),
    ]
    student_type = models.CharField(max_length=20, choices=STUDENT_TYPE_CHOICES)
    discount_percent = models.FloatField()  
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE,null=True,blank=True)

    def clean(self):
        if not (0 <= self.discount_percent <= 100):
            raise ValidationError("Discount percentage must be between 0 and 100.")


class Payment(models.Model):
      
    PENDING = 'pending'
    COMPLETED = 'completed'
    
    PAYMENT_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
    ]


    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2 )
    payment_date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default=PENDING,  
    )

    def apply_discount(self):
        applicable_discount = Discount.objects.filter(student_type='Scholarship', student=self.student)
        if applicable_discount:
            discount_percent = applicable_discount.first().discount_percent
            self.amount_paid -= self.amount_paid * (discount_percent / 100)


class Invoice(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    invoice_date = models.DateField(auto_now_add=True)

    def calculate_total(self):
        fee_types = self.student.get_fee_for_class()
        total = sum(fee.amount for fee in fee_types)
        
        applicable_discount = Discount.objects.filter(student_type='Scholarship', student=self.student)
        if applicable_discount:
            discount_percent = applicable_discount.first().discount_percent
            total -= total * (discount_percent / 100)

        self.total_amount = total


class Driver(models.Model):
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    license_number = models.CharField(max_length=50, unique=True)
    dob = models.DateField(default=timezone.now)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to="driver_photos/", blank=True, null=True)


class BusAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="bus_assignments")
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    pickup_point = models.CharField(max_length=100, blank=True)
    dropoff_point = models.CharField(max_length=100, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

class SchoolNews(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Event(models.Model):
    name = models.CharField(max_length=100)  
    description = models.TextField(null=True, blank=True)
    event_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    event_image = models.ImageField(upload_to='event_images/', null=True, blank=True)  


class EventRegistration(models.Model):
    event = models.ForeignKey(Event, related_name='registrations', on_delete=models.CASCADE)
    student_name = models.CharField(max_length=255)
    student_email = models.EmailField()
    registration_date = models.DateTimeField(auto_now_add=True)


class EventResult(models.Model):
    event = models.ForeignKey(Event, related_name='results', on_delete=models.CASCADE)
    student_name = models.CharField(max_length=255)
    result = models.CharField(max_length=255)
    score = models.FloatField()

    
    def __str__(self):
        return f"Result of {self.student_name} in {self.event.title}"


class Message(models.Model):
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-sent_at'] 

class DisciplinaryRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    incident_date = models.DateField()
    description = models.TextField()
    action_taken = models.CharField(max_length=200)
    severity = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')])
    remarks = models.TextField(null=True, blank=True)
