from django.db import models
from django.utils import timezone
import uuid

# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True, default='GEN', help_text="Department code for roll number generation")
    head = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Session(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    session_name = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.session_name} ({self.start_date.year}-{self.end_date.year})"
    
    class Meta:
        ordering = ['-created_at']

class Student(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)  # Personal email (displayed in form)
    college_email = models.EmailField(unique=True, blank=True, null=True)  # College email (hidden, used for login)
    password = models.CharField(max_length=100, blank=True, null=True)  # Store generated password
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField()
    enrollment_date = models.DateField(auto_now_add=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    student_id = models.CharField(max_length=15, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Additional fields for complete student information
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], blank=True, null=True)
    student_image = models.ImageField(upload_to='student_images/', blank=True, null=True)
    father_name = models.CharField(max_length=50, blank=True, null=True)
    father_occupation = models.CharField(max_length=50, blank=True, null=True)
    father_image = models.ImageField(upload_to='father_images/', blank=True, null=True)
    mother_name = models.CharField(max_length=50, blank=True, null=True)
    mother_occupation = models.CharField(max_length=50, blank=True, null=True)
    mother_image = models.ImageField(upload_to='mother_images/', blank=True, null=True)
    hobby = models.CharField(max_length=100, blank=True, null=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True)
    aim_of_life = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    course = models.CharField(max_length=50, blank=True, null=True)
    department = models.CharField(max_length=50, blank=True, null=True)
    semester = models.CharField(max_length=20, blank=True, null=True)
    batch = models.CharField(max_length=20, blank=True, null=True)
    
    # Academic information
    tenth_board = models.CharField(max_length=50, blank=True, null=True)
    tenth_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    tenth_year = models.IntegerField(blank=True, null=True)
    
    twelfth_board = models.CharField(max_length=50, blank=True, null=True)
    twelfth_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    twelfth_year = models.IntegerField(blank=True, null=True)
    
    # Diploma information
    diploma_course = models.CharField(max_length=100, blank=True, null=True)
    diploma_institution = models.CharField(max_length=200, blank=True, null=True)
    diploma_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    diploma_year = models.IntegerField(blank=True, null=True)
    
    graduation_degree = models.CharField(max_length=100, blank=True, null=True)
    graduation_university = models.CharField(max_length=200, blank=True, null=True)
    graduation_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    graduation_status = models.CharField(max_length=20, blank=True, null=True)
    
    # Rejection reason (if rejected)
    rejection_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id if self.student_id else 'Pending ID'})"
    
    class Meta:
        ordering = ['-registration_date']

class Teacher(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100, blank=True, null=True)  # Store generated password
    teacher_id = models.CharField(max_length=15, unique=True, default="TCH00001")
    teacher_code = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    years_of_experience = models.IntegerField(default=0)
    date_of_birth = models.DateField()
    hire_date = models.DateField(auto_now_add=True)
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.teacher_id})"

class Course(models.Model):
    course_name = models.CharField(max_length=100, unique=True)
    duration = models.IntegerField(help_text="Duration in years", default=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course_name']
    
    def __str__(self):
        return self.course_name

class Subject(models.Model):
    SUBJECT_TYPES = (
        ('core', 'Core Subject'),
        ('elective', 'Elective Subject'),
        ('practical', 'Practical Subject'),
    )
    
    subject_code = models.CharField(max_length=20, unique=True)
    subject_name = models.CharField(max_length=100)
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPES, default='core')
    description = models.TextField(blank=True, null=True)
    credits = models.IntegerField(default=3)
    semester = models.IntegerField(default=1, help_text="Semester in which this subject is taught")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='subjects')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name='subjects')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_subjects')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['semester', 'subject_code']
        unique_together = [['subject_name', 'department']]  # Allow same subject name in different departments
    
    def __str__(self):
        dept_name = self.department.name if self.department else 'No Dept'
        return f"{self.subject_code} - {self.subject_name} ({dept_name}) - Sem {self.semester}"

class Batch(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('inactive', 'Inactive'),
    ]
    
    PAYMENT_CHOICES = [
        ('full', 'Full Payment'),
        ('installment', 'Installments'),
    ]
    
    name = models.CharField(max_length=50)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='batches')
    admission_year = models.IntegerField()
    duration = models.IntegerField(help_text="Duration in years")
    total_course_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total course fee")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='full', help_text="Payment type")
    number_of_installments = models.IntegerField(null=True, blank=True, help_text="Number of installments if payment type is installment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-admission_year', 'name']
        unique_together = ['department', 'admission_year']
    
    def __str__(self):
        end_year = self.admission_year + self.duration
        return f"{self.course.course_name} - {self.department.name} ({self.admission_year}–{end_year})"

class Timetable(models.Model):
    DAY_CHOICES = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
    ]
    
    TIME_SLOT_CHOICES = [
        ('09-10', '09:00 - 10:00'),
        ('10-11', '10:00 - 11:00'),
        ('11-12', '11:00 - 12:00'),
        ('12-01', '12:00 - 01:00'),
        ('01-02', '01:00 - 02:00'),
        ('02-03', '02:00 - 03:00'),
        ('03-04', '03:00 - 04:00'),
    ]
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='timetables')
    semester = models.IntegerField()
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    time_slot = models.CharField(max_length=5, choices=TIME_SLOT_CHOICES)
    subject = models.CharField(max_length=100)
    room = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['department', 'semester', 'day', 'time_slot']
        ordering = ['department', 'semester', 'day', 'time_slot']
    
    def __str__(self):
        return f"{self.department.name} - Sem {self.semester} - {self.get_day_display()} - {self.get_time_slot_display()} - {self.subject}"

class Book(models.Model):
    """Book model for library management"""
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True, help_text="International Standard Book Number")
    publisher = models.CharField(max_length=100)
    publication_year = models.IntegerField()
    category = models.CharField(max_length=50)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    description = models.TextField(blank=True, null=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    
    # Link to subject
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='books')
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title} by {self.author} ({self.isbn})"

class BookIssue(models.Model):
    """Book issue tracking model"""
    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_issues')
    
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    
    # Additional fields
    remarks = models.TextField(blank=True, null=True)
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.book.title} - {self.student.first_name} ({self.status})"
    
    def is_overdue(self):
        from datetime import date
        return self.status == 'issued' and date.today() > self.due_date

class Admin(models.Model):
    ROLE_CHOICES = [
        ('primary', 'Primary Admin'),
        ('admin', 'Admin'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # In production, use proper hashing
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_primary_admin(self):
        return self.role == 'primary' and self.status == 'active'

class Payment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
        ('card', 'Card Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='cash')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    installment_number = models.IntegerField(null=True, blank=True, help_text="Installment number if applicable")
    created_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment {self.id} - {self.student.first_name} {self.student.last_name} - ₹{self.amount}"

class PasswordResetToken(models.Model):
    """Model to store password reset tokens"""
    user_type = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('teacher', 'Teacher')])
    user_id = models.IntegerField()  # Store the ID of the user (admin or teacher)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Password reset token for {self.user_type} - {self.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class Quiz(models.Model):
    """Quiz model for creating and managing quizzes"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    semester = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration_minutes = models.IntegerField(help_text='Quiz duration in minutes')
    total_questions = models.IntegerField(default=0)
    total_marks = models.DecimalField(decimal_places=2, default=0.0, max_digits=6)
    passing_marks = models.DecimalField(decimal_places=2, default=0.0, max_digits=6)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    shuffle_questions = models.BooleanField(default=False)
    show_results_immediately = models.BooleanField(default=True)
    instructions = models.TextField(blank=True, null=True)
    
    # Foreign keys
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='quizzes')
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.title} - {self.subject.subject_name} ({self.department.name})"
    
    def is_active_now(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def is_upcoming(self):
        from django.utils import timezone
        return self.is_active and self.start_date > timezone.now()
    
    def has_student_attempted(self, student):
        return self.attempts.filter(student=student).exists()

class QuizQuestion(models.Model):
    """Quiz question model"""
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    marks = models.DecimalField(decimal_places=2, default=1.0, max_digits=5)
    order = models.IntegerField(default=1)
    
    # Foreign key
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Question {self.order} - {self.quiz.title}"

class QuizOption(models.Model):
    """Quiz option model for multiple choice questions"""
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=1)
    
    # Foreign keys
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Option {self.order} - {self.question.question_text[:50]}"

class QuizAttempt(models.Model):
    """Quiz attempt model to track student attempts"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]
    
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    marks_obtained = models.DecimalField(decimal_places=2, max_digits=6, blank=True, null=True)
    percentage = models.DecimalField(decimal_places=2, max_digits=5, blank=True, null=True)
    total_time_taken = models.IntegerField(blank=True, help_text='Time taken in seconds', null=True)
    
    # Foreign keys
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_attempts')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['quiz', 'student']
    
    def __str__(self):
        return f"{self.student.first_name} - {self.quiz.title} ({self.status})"
    
    def is_completed(self):
        return self.status == 'completed'
    
    def can_be_started(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.status == 'not_started' and 
                self.quiz.is_active and 
                self.quiz.start_date <= now <= self.quiz.end_date)

class QuizAnswer(models.Model):
    """Quiz answer model to store student answers"""
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(blank=True, null=True)
    marks_obtained = models.DecimalField(decimal_places=2, max_digits=5, blank=True, null=True)
    
    # Foreign keys
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuizOption, on_delete=models.CASCADE, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"Answer for {self.question.question_text[:50]} by {self.attempt.student.first_name}"