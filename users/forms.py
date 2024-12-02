from django import forms
from .models import Student
from .models import FeeType,LeaveRequest,TeacherAttendance,StudentAttendance
from django import forms
from .models import Message, UserProfile,Student,SchoolClass
from django import forms
from .models import StudentAttendance, SchoolClass, Student
from django.utils import timezone  
from django import forms
from .models import Message, UserProfile,Student,SchoolClass,Exam,ExamGrade,Teacher,BusAssignment

class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6, 
        min_length=6,
        widget=forms.TextInput(attrs={'placeholder': 'Enter OTP', 'class': 'form-control'}),
        required=True
    )


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['photo']
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class TeacherAttendanceForm(forms.ModelForm):
    class Meta:
        model = TeacherAttendance
        fields = ['teacher', 'date', 'status']
    

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['reason', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        }


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'date', 'room', 'course', 'exam_type', 'total_marks']


class ExamGradeForm(forms.ModelForm):
    class Meta:
        model = ExamGrade
        fields = ['student', 'exam', 'marks']


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['address', 'qualification', 'dob', 'contact', 'resume', 'courses']


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['address', 'school_class', 'dob', 'photo', 'course', 'hobbies']


class BusAssignmentForm(forms.ModelForm):
    class Meta:
        model = BusAssignment
        fields = ['student', 'bus', 'pickup_point', 'dropoff_point']


class PaymentForm(forms.Form):
    fee_types = forms.ModelMultipleChoiceField(
        queryset=FeeType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )


class AttendanceForm(forms.ModelForm):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.all(), label='Select Class')
    student = forms.ModelChoiceField(queryset=Student.objects.all(), label='Select Student')
    date = forms.DateField(widget=forms.SelectDateWidget(), initial=timezone.now().date())  # Ensure correct usage of timezone.now().date()
    status = forms.ChoiceField(choices=[('Present', 'Present'), ('Absent', 'Absent')], initial='Present')

    class Meta:
        model = StudentAttendance
        fields = ['school_class', 'student', 'date', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'school_class' in self.data:
            school_class_id = self.data.get('school_class')
            self.fields['student'].queryset = Student.objects.filter(school_class_id=school_class_id)
        else:
            self.fields['student'].queryset = Student.objects.none()


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'content']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  
        super().__init__(*args, **kwargs)

       
        if user.profile.role == 'parent':
            self.fields['recipient'].queryset = UserProfile.objects.filter(role='teacher')
        elif user.profile.role == 'teacher':
            self.fields['recipient'].queryset = UserProfile.objects.filter(role='parent')

        
    
        self.fields['recipient'].label_from_instance = lambda obj: f"{obj.user.username} ({obj.role})"

