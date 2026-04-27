from urllib import request
import requests
from bs4 import BeautifulSoup

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Max, Q
from django.db import models
from .models import Student, Teacher, Session, Subject, Course, Department, Batch, Timetable, Book, BookIssue, Admin, Payment, PasswordResetToken, Quiz, QuizAttempt, QuizQuestion, QuizOption, QuizAnswer
from django.http import JsonResponse
import json
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.conf import settings
import uuid


def generate_subject_code(subject_name, department_id, course_id, semester):
    """
    Generate a meaningful subject code based on department, course, and subject name
    Format: [DEPT_CODE][SEMESTER][SUBJECT_ABBR]
    Example: CS101MATH for Computer Science, Semester 1, Mathematics
    """
    try:
        # Get department code
        dept_code = 'GEN'
        if department_id:
            department = Department.objects.get(id=department_id)
            dept_code = department.code.upper() if department.code else 'GEN'
        
        # Get semester number
        sem_num = '1'
        if semester:
            # Extract just the number from semester (e.g., "Semester 1" -> "1")
            sem_num = str(semester).replace('Semester ', '').replace('sem', '')[:1]
            if not sem_num.isdigit():
                sem_num = '1'
        
        # Generate subject abbreviation
        subject_abbr = ''
        if subject_name:
            # Take first 3-4 letters of important words
            words = subject_name.upper().replace('AND', '').replace('OF', '').split()
            if len(words) >= 2:
                # Take first 2 letters from first two words
                subject_abbr = words[0][:2] + words[1][:2]
            elif len(words) == 1:
                # Take first 4 letters from single word
                subject_abbr = words[0][:4]
            else:
                subject_abbr = 'SUBJ'
        else:
            subject_abbr = 'SUBJ'
        
        # Combine to create subject code
        base_code = f"{dept_code}{sem_num}{subject_abbr}"
        
        # Ensure uniqueness by adding suffix if needed
        counter = 1
        final_code = base_code
        while Subject.objects.filter(subject_code=final_code).exists():
            final_code = f"{base_code}{counter}"
            counter += 1
        
        return final_code
        
    except Exception as e:
        # Fallback to simple generation if anything goes wrong
        fallback_code = subject_name.upper().replace(' ', '_')[:10] if subject_name else 'SUBJ'
        counter = 1
        while Subject.objects.filter(subject_code=fallback_code).exists():
            fallback_code = f"{fallback_code}_{counter}"
            counter += 1
        return fallback_code



def generate_student_password():
    """Generate a random password for student"""
    import random
    import string
    length = 8
    characters = string.ascii_letters + string.digits + '!@#$%'
    password = ''.join(random.choice(characters) for i in range(length))
    return password


def send_student_approval_email(student):
    """Send approval email to student"""
    try:
        # Generate password for student
        password = generate_student_password()
        
        # Store password in database
        student.password = password
        student.save()
        
        subject = "Student Registration Approved - Student 360 Platform"
        message = f"""
Dear {student.first_name} {student.last_name},

Congratulations! Your registration has been approved.

Student Details:
- Student ID: {student.student_id}
- Course: {student.course}
- Department: {student.department}
- Semester: {student.semester}
- Batch: {student.batch}

Login Credentials:
- Email: {student.college_email}
- Password: {password}

You can now access the Student 360 Platform using your college email and password.

Login URL: {request.build_absolute_uri('/')}

Best regards,
Student 360 Platform Administration
        """
        
        send_mail(
            subject,
            message,
            'annonmusk00@gmail.com',
            [student.email],  # Send to personal email
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending approval email: {e}")
        return False

def send_teacher_welcome_email(teacher):
    """Send welcome email to newly added teacher"""
    try:
        # Generate password for teacher
        password = generate_student_password()  # Reuse the same password generation function
        
        # Store password in database
        teacher.password = password
        teacher.save()
        
        subject = "Welcome to Student 360 Platform - Teacher Account Created"
        message = f"""
Dear {teacher.first_name} {teacher.last_name},

Welcome to the Student 360 Platform! Your teacher account has been successfully created.

Teacher Details:
- Teacher ID: {teacher.teacher_id}
- Teacher Code: {teacher.teacher_code}
- Department: {teacher.department.name if teacher.department else 'Not Assigned'}
- Years of Experience: {teacher.years_of_experience}

Login Credentials:
- Email: {teacher.email}
- Password: {password}

You can now access the Student 360 Platform using your email and password.

Login URL: {request.build_absolute_uri('/')}

Your teacher code ({teacher.teacher_code}) will be required for certain administrative functions.

Best regards,
Student 360 Platform Administration
        """
        
        send_mail(
            subject,
            message,
            'annonmusk00@gmail.com',
            [teacher.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending teacher welcome email: {e}")
        return False


def generate_college_email(first_name, last_name, student_id, department=None, admission_year=None):
    """Generate college email in format: year + branch + serialno@bcet.in"""
    try:
        # Get admission year (last 2 digits)
        if admission_year:
            year_part = str(admission_year)[-2:]
        else:
            year_part = "25"  # Default to current year
        
        # Get department code (branch)
        if department:
            # Try to get department object to get code
            try:
                from student.models import Department
                dept_obj = Department.objects.get(name=department)
                branch_part = (dept_obj.code or 'GEN').lower()
            except Department.DoesNotExist:
                # Fallback to first 3 letters of department name
                branch_part = department[:3].lower() if department else 'gen'
        else:
            branch_part = 'gen'
            print(f"DEBUG: Department is None, using 'gen' for student {first_name} {last_name}")
        
        # Generate serial number (count existing students with same year and department)
        try:
            existing_count = Student.objects.filter(
                college_email__startswith=f"{year_part}{branch_part}"
            ).count()
            serial_part = str(existing_count + 1).zfill(2)
        except:
            serial_part = "01"
        
        email = f"{year_part}{branch_part}{serial_part}@bcet.in"
        print(f"DEBUG: Generated email {email} for department '{department}' -> branch_part '{branch_part}'")
        return email
    except Exception as e:
        # Fallback format
        import random
        random_num = random.randint(1000, 9999)
        return f"25gen{random_num}@bcet.in"


# Create your views here.

def index_page(request):
    """
    Landing page view for Student 360 Platform
    Shows project information and login form
    """
    return render(request, 'index.html')


def register(request):

    if request.method == 'POST':

        # Get form data

        first_name = request.POST.get('firstName')

        last_name = request.POST.get('lastName')

        gender = request.POST.get('gender')

        date_of_birth = request.POST.get('dateOfBirth')

        email = request.POST.get('email')

        # Validate required fields
        if not email or not email.strip():
            return JsonResponse({
                'success': False,
                'message': 'Email address is required'
            })
        
        # Basic email format validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address'
            })

        student_id = request.POST.get('studentId')

        course = request.POST.get('course')

        semester = request.POST.get('semester')

        batch = request.POST.get('batch')

        

        # 10th grade details

        tenth_board = request.POST.get('tenthBoard')

        tenth_percentage = request.POST.get('tenthPercentage')

        tenth_year = request.POST.get('tenthYear')

        

        # 12th grade details

        twelfth_board = request.POST.get('twelfthBoard')

        twelfth_percentage = request.POST.get('twelfthPercentage')

        twelfth_year = request.POST.get('twelfthYear')

        

        # Diploma details

        diploma_course = request.POST.get('diplomaCourse')

        diploma_institution = request.POST.get('diplomaInstitution')

        diploma_percentage = request.POST.get('diplomaPercentage')

        diploma_year = request.POST.get('diplomaYear')

        

        # Graduate details

        graduation_degree = request.POST.get('graduationDegree')

        graduation_university = request.POST.get('graduationUniversity')

        graduation_percentage = request.POST.get('graduationPercentage')

        graduation_year = request.POST.get('graduationYear')

        graduation_status = request.POST.get('graduationStatus')

        

        # Create student record with pending status

        try:

            # Convert empty strings to None for decimal fields

            tenth_percentage = float(tenth_percentage) if tenth_percentage and tenth_percentage.strip() else None

            twelfth_percentage = float(twelfth_percentage) if twelfth_percentage and twelfth_percentage.strip() else None

            graduation_percentage = float(graduation_percentage) if graduation_percentage and graduation_percentage.strip() else None

            diploma_percentage = float(diploma_percentage) if diploma_percentage and diploma_percentage.strip() else None

            

            # Convert empty strings to None for integer fields

            tenth_year = int(tenth_year) if tenth_year and tenth_year.strip() else None

            twelfth_year = int(twelfth_year) if twelfth_year and twelfth_year.strip() else None

            graduation_year = int(graduation_year) if graduation_year and graduation_year.strip() else None

            diploma_year = int(diploma_year) if diploma_year and diploma_year.strip() else None

            

            student = Student.objects.create(

                first_name=first_name,

                
                last_name=last_name,

                email=email,  # Personal email (displayed in form)
                college_email=college_email,  # College email (hidden, used for login)

                mobile_no=mobile_no if mobile_no and mobile_no.strip() else None,

                date_of_birth=date_of_birth,

                student_id=student_id,

                gender=gender if gender and gender.strip() else None,

                course=course if course and course.strip() else None,

                semester=semester if semester and semester.strip() else None,

                batch=batch if batch and batch.strip() else None,

                tenth_board=tenth_board if tenth_board and tenth_board.strip() else None,

                tenth_percentage=tenth_percentage,

                tenth_year=tenth_year,

                twelfth_board=twelfth_board if twelfth_board and twelfth_board.strip() else None,

                twelfth_percentage=twelfth_percentage,

                twelfth_year=twelfth_year,

                diploma_course=diploma_course if diploma_course and diploma_course.strip() else None,

                diploma_institution=diploma_institution if diploma_institution and diploma_institution.strip() else None,

                diploma_percentage=diploma_percentage,

                diploma_year=diploma_year,

                graduation_degree=graduation_degree if graduation_degree and graduation_degree.strip() else None,

                graduation_university=graduation_university if graduation_university and graduation_university.strip() else None,

                graduation_percentage=graduation_percentage,

                graduation_year=graduation_year,

                graduation_status=graduation_status if graduation_status and graduation_status.strip() else None,

                status='approved'  # Admin-added students are approved immediately

            )

            

            # Show success message

            from django.contrib import messages

            messages.success(request, f'Student {student.first_name} {student.last_name} ({student.student_id if student.student_id else "Pending ID"}) registered successfully! Your application is now pending approval.')

            return render(request, 'register.html')

            

        except Exception as e:

            from django.contrib import messages

            messages.error(request, f'Error registering student: {str(e)}')

            return render(request, 'register.html')

    

    return render(request, 'register.html')



def admin_register_student(request):

    if request.method == 'POST':

        # Get form data

        first_name = request.POST.get('firstName')

        last_name = request.POST.get('lastName')

        gender = request.POST.get('gender')

        date_of_birth = request.POST.get('dateOfBirth')

        email = request.POST.get('studentEmail')

        mobile_no = request.POST.get('mobileNo')

        student_id = request.POST.get('studentId')

        # Check if email already exists
        if Student.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'A student with this email address already exists. Please use a different email.'
            })

        # Generate college email automatically
        batch = request.POST.get('batch')
        
        # Extract admission year and department from batch if available
        admission_year = None
        department = None
        if batch:
            try:
                # Try to get batch object to extract admission year and department
                from student.models import Batch
                batch_obj = Batch.objects.get(id=int(batch))
                admission_year = batch_obj.admission_year
                department = batch_obj.department.name  # Get department name from batch
            except (Batch.DoesNotExist, ValueError):
                pass
        
        college_email = generate_college_email(first_name, last_name, student_id, department, admission_year)

        course = request.POST.get('course')

        semester = request.POST.get('semester')

        batch = request.POST.get('batch')

        student_image = request.FILES.get('studentImage')

        father_name = request.POST.get('fatherName')

        father_occupation = request.POST.get('fatherOccupation')

        father_image = request.FILES.get('fatherImage')

        mother_name = request.POST.get('motherName')

        mother_occupation = request.POST.get('motherOccupation')

        mother_image = request.FILES.get('motherImage')

        hobby = request.POST.get('hobby')

        blood_group = request.POST.get('bloodGroup')

        aim_of_life = request.POST.get('aimOfLife')

        address = request.POST.get('address')

        

        # 10th grade details

        tenth_board = request.POST.get('tenthBoard')

        tenth_percentage = request.POST.get('tenthPercentage')

        tenth_year = request.POST.get('tenthYear')

        

        # 12th grade details

        twelfth_board = request.POST.get('twelfthBoard')

        twelfth_percentage = request.POST.get('twelfthPercentage')

        twelfth_year = request.POST.get('twelfthYear')

        

        # Diploma details

        diploma_course = request.POST.get('diplomaCourse')

        diploma_institution = request.POST.get('diplomaInstitution')

        diploma_percentage = request.POST.get('diplomaPercentage')

        diploma_year = request.POST.get('diplomaYear')

        

        # Graduate details

        graduation_degree = request.POST.get('graduationDegree')

        graduation_university = request.POST.get('graduationUniversity')

        graduation_percentage = request.POST.get('graduationPercentage')

        graduation_year = request.POST.get('graduationYear')

        graduation_status = request.POST.get('graduationStatus')

        

        # Create student record with pending status

        try:

            # Convert empty strings to None for decimal fields

            tenth_percentage = float(tenth_percentage) if tenth_percentage and tenth_percentage.strip() else None

            twelfth_percentage = float(twelfth_percentage) if twelfth_percentage and twelfth_percentage.strip() else None

            graduation_percentage = float(graduation_percentage) if graduation_percentage and graduation_percentage.strip() else None

            diploma_percentage = float(diploma_percentage) if diploma_percentage and diploma_percentage.strip() else None

            

            # Convert empty strings to None for integer fields

            tenth_year = int(tenth_year) if tenth_year and tenth_year.strip() else None

            twelfth_year = int(twelfth_year) if twelfth_year and twelfth_year.strip() else None

            graduation_year = int(graduation_year) if graduation_year and graduation_year.strip() else None

            diploma_year = int(diploma_year) if diploma_year and diploma_year.strip() else None

            

            student = Student.objects.create(

                first_name=first_name,

                
                last_name=last_name,

                email=email,  # Personal email (displayed in form)
                college_email=college_email,  # College email (hidden, used for login)

                mobile_no=mobile_no if mobile_no and mobile_no.strip() else None,

                date_of_birth=date_of_birth,

                student_id=student_id,

                gender=gender if gender and gender.strip() else None,

                course=course if course and course.strip() else None,

                semester=semester if semester and semester.strip() else None,

                batch=batch if batch and batch.strip() else None,

                student_image=student_image,

                father_name=father_name if father_name and father_name.strip() else None,

                father_occupation=father_occupation if father_occupation and father_occupation.strip() else None,

                father_image=father_image,

                mother_name=mother_name if mother_name and mother_name.strip() else None,

                mother_occupation=mother_occupation if mother_occupation and mother_occupation.strip() else None,

                mother_image=mother_image,

                hobby=hobby if hobby and hobby.strip() else None,

                blood_group=blood_group if blood_group and blood_group.strip() else None,

                aim_of_life=aim_of_life if aim_of_life and aim_of_life.strip() else None,

                address=address if address and address.strip() else None,

                tenth_board=tenth_board if tenth_board and tenth_board.strip() else None,

                tenth_percentage=tenth_percentage,

                tenth_year=tenth_year,

                twelfth_board=twelfth_board if twelfth_board and twelfth_board.strip() else None,

                twelfth_percentage=twelfth_percentage,

                twelfth_year=twelfth_year,

                diploma_course=diploma_course if diploma_course and diploma_course.strip() else None,

                diploma_institution=diploma_institution if diploma_institution and diploma_institution.strip() else None,

                diploma_percentage=diploma_percentage,

                diploma_year=diploma_year,

                graduation_degree=graduation_degree if graduation_degree and graduation_degree.strip() else None,

                graduation_university=graduation_university if graduation_university and graduation_university.strip() else None,

                graduation_percentage=graduation_percentage,

                graduation_year=graduation_year,

                graduation_status=graduation_status if graduation_status and graduation_status.strip() else None,

                status='pending'  # Set status to pending by default

            )

            

            # Return JSON response for AJAX handling


            return JsonResponse({

                'success': True,

                'message': f'Student {first_name} {last_name} added successfully and is now visible in Student Management.',

                'student_id': student.id

            })

            

        except Exception as e:

            # Return JSON response for AJAX handling


            return JsonResponse({

                'success': False,

                'message': f'Error registering student: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })

def student_status(request):
    """Student dashboard view"""
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('login')
    
    try:
        student = Student.objects.get(college_email=student_email, status__in=['approved', 'pending'])
        
        # Fetch subjects based on student's department and current semester
        subjects = []
        if student.department and student.semester:
            try:
                # Get department object
                department = Department.objects.get(name=student.department)
                semester = int(student.semester)
                
                # Get unique subjects from timetable for this department and semester
                timetable_entries = Timetable.objects.filter(
                    department=department,
                    semester=semester
                ).values_list('subject', flat=True).distinct()
                
                # Get subject objects for these timetable entries
                subjects = Subject.objects.filter(
                    subject_name__in=timetable_entries,
                    is_active=True
                ).select_related('teacher').order_by('subject_code')
                
            except (Department.DoesNotExist, ValueError):
                subjects = []
        
        # Fetch timetable entries for student's department and semester
        timetable_entries = []
        if student.department and student.semester:
            try:
                # Get department object
                department = Department.objects.get(name=student.department)
                semester = int(student.semester)
                
                # Filter timetable entries
                timetable_entries = Timetable.objects.filter(
                    department=department,
                    semester=semester
                ).order_by('day', 'time_slot')
            except (Department.DoesNotExist, ValueError):
                timetable_entries = []
        
        # Fetch available quizzes for the student
        available_quizzes = []
        attempted_quizzes = []
        if student.department and student.semester:
            try:
                # Get department object for quizzes - try by name first, then by code if needed
                department = None
                
                # Try to get department by name
                try:
                    department = Department.objects.get(name=student.department)
                except Department.DoesNotExist:
                    # If not found by name, try to get by code (some students might have dept code stored)
                    try:
                        department = Department.objects.get(code=student.department)
                    except Department.DoesNotExist:
                        # Fallback to first department if available
                        department = Department.objects.first()
                        if not department:
                            department = Department.objects.create(name=student.department, code=student.department[:3].upper())
                
                # Better semester conversion with error handling
                try:
                    # Handle different semester formats (e.g., "1", "Semester 1", "1st", "First")
                    semester_str = str(student.semester).strip().lower()
                    if semester_str.isdigit():
                        semester = int(semester_str)
                    elif 'sem' in semester_str:
                        # Extract number from "semester 1", "sem 1", etc.
                        import re
                        match = re.search(r'\d+', semester_str)
                        semester = int(match.group()) if match else 1
                    else:
                        # Try to convert directly
                        semester = int(semester_str)
                except (ValueError, AttributeError):
                    # Default to semester 1 if conversion fails
                    semester = 1
                
                # Get all active quizzes for student's department and semester
                all_quizzes = Quiz.objects.filter(
                    department=department,
                    semester=semester,
                    is_active=True
                ).select_related('subject', 'teacher').order_by('-created_date')
                
                # DEBUG: Print quiz filtering info
                print(f"DEBUG: Student department: {student.department}")
                print(f"DEBUG: Student semester: {semester}")
                print(f"DEBUG: Found department: {department.name if department else 'None'}")
                print(f"DEBUG: Total quizzes found: {all_quizzes.count()}")
                for quiz in all_quizzes:
                    print(f"DEBUG: Quiz - {quiz.title}, Dept: {quiz.department.name}, Sem: {quiz.semester}")
                
                # Debug information
                print(f"DEBUG: Student {student.first_name} {student.last_name}")
                print(f"DEBUG: Student department: {student.department}")
                print(f"DEBUG: Student semester: {semester}")
                print(f"DEBUG: Found department: {department.name if department else 'None'}")
                print(f"DEBUG: Found {all_quizzes.count()} quizzes for this student")
                print(f"DEBUG: Current server time: {timezone.now()}")
                
                for quiz in all_quizzes:
                    print(f"DEBUG: Quiz - {quiz.title}, Dept: {quiz.department.name}, Sem: {quiz.semester}")
                    print(f"DEBUG: Quiz start: {quiz.start_date}, Quiz end: {quiz.end_date}")
                    print(f"DEBUG: Quiz is_active: {quiz.is_active}")
                    print(f"DEBUG: Quiz is_active_now(): {quiz.is_active_now()}")
                    print(f"DEBUG: Quiz is_upcoming(): {quiz.is_upcoming()}")
                    
                    # Check if student can access this quiz
                    can_access = False
                    if quiz.department == department and str(quiz.semester) == str(semester):
                        can_access = True
                    
                    if can_access:
                        # Check if student has already attempted this quiz
                        attempt = QuizAttempt.objects.filter(quiz=quiz, student=student).first()
                        
                        quiz_data = {
                            'id': quiz.id,
                            'title': quiz.title,
                            'subject': quiz.subject.subject_name,
                            'teacher': f"{quiz.teacher.first_name} {quiz.teacher.last_name}",
                            'start_date': timezone.localtime(quiz.start_date),
                            'end_date': timezone.localtime(quiz.end_date),
                            'duration_minutes': quiz.duration_minutes,
                            'total_questions': quiz.total_questions,
                            'total_marks': quiz.total_marks,
                            'instructions': quiz.instructions,
                            'attempt_id': attempt.id if attempt else None,
                            'attempt_status': attempt.status if attempt else 'not_started',
                            'percentage': attempt.percentage if attempt and attempt.percentage else None,
                            'is_active_now': quiz.is_active_now(),
                            'is_upcoming': quiz.is_upcoming(),
                        }
                        
                        if attempt:
                            # Get the attempt details
                            attempt = QuizAttempt.objects.get(quiz=quiz, student=student)
                            quiz_data.update({
                                'attempt_status': attempt.status,
                                'marks_obtained': attempt.marks_obtained,
                                'percentage': attempt.percentage,
                                'attempt_id': attempt.id
                            })
                            attempted_quizzes.append(quiz_data)
                        else:
                            available_quizzes.append(quiz_data)
                    else:
                        available_quizzes.append(quiz_data)
                        
            except Exception as e:
                # Log the error and try fallback approach
                print(f"ERROR in quiz filtering: {str(e)}")
                
                # Fallback: Try to get quizzes without semester filter if department exists
                try:
                    department = Department.objects.filter(name=student.department).first()
                    if department:
                        all_quizzes = Quiz.objects.filter(
                            department=department,
                            is_active=True
                        ).select_related('subject', 'teacher').order_by('-created_date')
                        
                        print(f"FALLBACK: Found {all_quizzes.count()} quizzes for department {department.name} (no semester filter)")
                        
                        # Get student's quiz attempts
                        student_attempts = QuizAttempt.objects.filter(
                            student=student
                        ).values_list('quiz_id', flat=True)
                        
                        # Separate quizzes into available and attempted
                        for quiz in all_quizzes:
                            quiz_data = {
                                'id': quiz.id,
                                'title': quiz.title,
                                'subject': quiz.subject.subject_name,
                                'teacher': f"{quiz.teacher.first_name} {quiz.teacher.last_name}",
                                'start_date': timezone.localtime(quiz.start_date),
                                'end_date': timezone.localtime(quiz.end_date),
                                'duration_minutes': quiz.duration_minutes,
                                'total_questions': quiz.total_questions,
                                'total_marks': quiz.total_marks,
                                'instructions': quiz.instructions,
                                'is_active_now': quiz.is_active_now(),
                                'is_upcoming': quiz.is_upcoming(),
                            }
                            
                            if quiz.id in student_attempts:
                                # Get attempt details
                                attempt = QuizAttempt.objects.get(quiz=quiz, student=student)
                                quiz_data.update({
                                    'attempt_status': attempt.status,
                                    'marks_obtained': attempt.marks_obtained,
                                    'percentage': attempt.percentage,
                                    'attempt_id': attempt.id
                                })
                                attempted_quizzes.append(quiz_data)
                            else:
                                available_quizzes.append(quiz_data)
                    else:
                        available_quizzes = []
                        attempted_quizzes = []
                except Exception as fallback_error:
                    print(f"FALLBACK also failed: {str(fallback_error)}")
                    available_quizzes = []
                    attempted_quizzes = []
        
        # Check for quiz results in session
        quiz_results = request.session.pop('quiz_results', None)
        
        context = {
            'student': student,
            'subjects': subjects,
            'timetable_entries': timetable_entries,
            'available_quizzes': available_quizzes,
            'attempted_quizzes': attempted_quizzes,
            'quiz_results': quiz_results,
            'subjects_json': json.dumps([{ 'subject_name': s.subject_name, 'subject_code': s.subject_code, 'credits': s.credits } for s in subjects]),
            'attempted_quizzes_json': json.dumps([{ 'subject': q.get('subject', ''), 'percentage': float(q.get('percentage', 0)) if q.get('percentage') else 0, 'title': q.get('title', '') } for q in attempted_quizzes])
        }
        
        # DEBUG: Print what's being passed to template
        print(f"DEBUG: Passing to template - Available quizzes: {len(available_quizzes)}, Attempted quizzes: {len(attempted_quizzes)}")
        if available_quizzes:
            print(f"DEBUG: First available quiz: {available_quizzes[0]}")
        
        return render(request, 'student_dashboard.html', context)
    except Student.DoesNotExist:
        return redirect('login')



def admin_dashboard(request):
    # Check if admin is logged in via session
    admin_username = request.session.get('admin_username')
    
    if not admin_username:
        return redirect('login')
    
    try:
        current_admin = Admin.objects.get(username=admin_username, status='active')
    except Admin.DoesNotExist:
        # Clear session and redirect to login if admin not found
        del request.session['admin_username']
        return redirect('login')

    students = Student.objects.all()
    pending_students = Student.objects.filter(status='pending')
    approved_students = Student.objects.filter(status='approved')
    teachers = Teacher.objects.all()
    admin_accounts = Admin.objects.all()
    departments = Department.objects.all()

    # Analytics Data
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Student enrollment by month (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    enrollment_data = Student.objects.filter(
        registration_date__gte=six_months_ago
    ).extra({
        'month': "strftime('%%Y-%%m', registration_date)"
    }).values('month').annotate(count=Count('id')).order_by('month')
    
    enrollment_months = []
    enrollment_counts = []
    for data in enrollment_data:
        enrollment_months.append(data['month'])
        enrollment_counts.append(data['count'])
    
    # Course distribution
    course_data = approved_students.values('course').annotate(count=Count('id')).order_by('-count')
    course_labels = []
    course_counts = []
    for data in course_data:
        if data['course']:
            course_labels.append(data['course'])
            course_counts.append(data['count'])
    
    # Academic performance by semester
    performance_data = approved_students.values('semester').annotate(
        total=Count('id'),
        passed=Count('id', filter=models.Q(status='approved'))
    ).order_by('semester')
    
    semester_labels = []
    passed_counts = []
    failed_counts = []
    for data in performance_data:
        if data['semester']:
            semester_labels.append(f"Semester {data['semester']}")
            passed_counts.append(data['passed'])
            failed_counts.append(data['total'] - data['passed'])

    # Department distribution
    department_data = approved_students.values('department').annotate(count=Count('id')).order_by('-count')
    department_labels = []
    department_counts = []
    for data in department_data:
        if data['department']:
            department_labels.append(data['department'])
            department_counts.append(data['count'])

    # Recent Activity Data
    recent_students = Student.objects.order_by('-registration_date')[:5]
    recent_teachers = Teacher.objects.order_by('-hire_date')[:3]
    recent_approved = Student.objects.filter(status='approved').order_by('-registration_date')[:3]

    context = {
        'students': students,  # Show all students in main list
        'pending_students': pending_students,  # Show pending students in approval section
        'teachers': teachers,
        'departments': departments,  # Add departments to context
        'current_admin': current_admin,
        'admin_accounts': admin_accounts,
        # Analytics data
        'enrollment_months': enrollment_months,
        'enrollment_counts': enrollment_counts,
        'course_labels': course_labels,
        'course_counts': course_counts,
        'semester_labels': semester_labels,
        'passed_counts': passed_counts,
        'failed_counts': failed_counts,
        'department_labels': department_labels,
        'department_counts': department_counts,
        # Recent activity data
        'recent_students': recent_students,
        'recent_teachers': recent_teachers,
        'recent_approved': recent_approved,
    }

    return render(request, 'admin_dashboard.html', context)

def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')
        user_role = request.POST.get('userRole')  # Get selected role
        

        # Check for admin credentials first
        if user_role == 'admin':
            try:
                admin = Admin.objects.get(username=username, status='active')
                
                # Check if password is hashed or plain text
                if admin.password.startswith('pbkdf2_sha256$'):
                    # Password is hashed, use check_password
                    if check_password(password, admin.password):
                        # Store admin username in session
                        request.session['admin_username'] = admin.username
                        # Update last login
                        admin.last_login = timezone.now()
                        admin.save()
                        return redirect('admin_dashboard')
                else:
                    # Password is still plain text, check directly
                    if password == admin.password:
                        # Store admin username in session
                        request.session['admin_username'] = admin.username
                        # Update last login
                        admin.last_login = timezone.now()
                        admin.save()
                        return redirect('admin_dashboard')
            except Admin.DoesNotExist:
                pass  # Admin not found
        
        # Fallback to hardcoded admin credentials for backward compatibility
        if user_role == 'admin' and username == 'admin@123' and password == 'admin123':
            # Create or get primary admin account
            admin, created = Admin.objects.get_or_create(
                username='admin@123',
                defaults={
                    'email': 'admin@school.edu',
                    'password': 'admin123',
                    'role': 'primary',
                    'status': 'active'
                }
            )
            if not created and admin.role != 'primary':
                admin.role = 'primary'
                admin.save()
            
            # Store admin username in session
            request.session['admin_username'] = admin.username
            # Update last login
            admin.last_login = timezone.now()
            admin.save()
            return redirect('admin_dashboard')

        # Check for teacher credentials
        elif user_role == 'teacher':
            try:
                teacher = Teacher.objects.get(email=username)
                
                # Check password - support both hashed and plain text passwords
                if teacher.password:
                    # Password is stored, check if it's hashed or plain text
                    if teacher.password.startswith('pbkdf2_sha256$'):
                        # Password is hashed, use check_password
                        if check_password(password, teacher.password):
                            # Store teacher email in session
                            request.session['teacher_email'] = teacher.email
                            # Redirect to teacher dashboard
                            return redirect('teacher')
                    else:
                        # Password is plain text, check directly
                        if password == teacher.password:
                            # Store teacher email in session
                            request.session['teacher_email'] = teacher.email
                            # Redirect to teacher dashboard
                            return redirect('teacher')
                elif password == teacher.teacher_code:
                    # Fallback for teachers created before password system
                    request.session['teacher_email'] = teacher.email
                    return redirect('teacher')

            except Teacher.DoesNotExist:
                teacher = None

        # Check for student credentials (college email + stored/default password)
        elif user_role == 'student':
            try:
                student = Student.objects.get(college_email=username, status__in=['approved', 'pending'])
                
                # Use stored password if available, otherwise use default password
                if student.password and password == student.password:
                    request.session['student_email'] = student.college_email
                    return redirect('student_status')
                elif not student.password and password == 'Student@123':
                    # For pending students without stored password, use default password
                    request.session['student_email'] = student.college_email
                    return redirect('student_status')
                # Temporary override for test student
                elif username == '26cse02@bcet.in' and password == 'Student@123':
                    request.session['student_email'] = student.college_email
                    return redirect('student_status')
            except Student.DoesNotExist:
                pass

        # If no role selected or invalid credentials
        return render(request, 'login.html', {'error': 'Invalid credentials or role selection'})

    
    
    return render(request, 'login.html')



def teacher_view(request):
    # Get all teachers for the list
    teachers = Teacher.objects.all()
    
    # Try to get current teacher from session or return first teacher as default
    current_teacher = None
    teacher_email = request.session.get('teacher_email')
    
    if teacher_email:
        try:
            current_teacher = Teacher.objects.get(email=teacher_email)
        except Teacher.DoesNotExist:
            pass
    
    # If no current teacher in session, use the first one as default
    if not current_teacher and teachers.exists():
        current_teacher = teachers.first()
    
    # Fetch students assigned to the current teacher
    assigned_students = []
    if current_teacher:
        # Get students based on teacher's department and subjects
        if current_teacher.department:
            # Get students in the same department as the teacher
            assigned_students = Student.objects.filter(
                department=current_teacher.department.name,
                status='approved'
            ).order_by('first_name', 'last_name')
        
        # Also get students from subjects taught by this teacher
        taught_subjects = Subject.objects.filter(teacher=current_teacher)
        for subject in taught_subjects:
            # Get students in the same department and semester as the subject
            subject_students = Student.objects.filter(
                department=subject.department.name if subject.department else None,
                semester=str(subject.semester),
                status='approved'
            ).order_by('first_name', 'last_name')
            
            # Add unique students to the list
            for student in subject_students:
                if student not in assigned_students:
                    assigned_students.append(student)
    
    # Fetch timetable entries for the teacher
    timetable_entries = []
    if current_teacher:
        # Get subjects taught by this teacher
        taught_subjects = Subject.objects.filter(teacher=current_teacher)
        
        # Get timetable entries that match the teacher's subjects and department
        if current_teacher.department and taught_subjects.exists():
            # Create a set to track unique entries and avoid duplicates
            seen_entries = set()
            
            for subject in taught_subjects:
                # Filter timetable entries by department, semester, and exact subject name match
                subject_timetables = Timetable.objects.filter(
                    department=current_teacher.department,
                    semester=subject.semester,
                    subject=subject.subject_name  # Exact match for subject name
                ).order_by('day', 'time_slot')
                
                # Add unique entries to avoid duplicates
                for entry in subject_timetables:
                    # Create a unique identifier for each entry
                    entry_id = f"{entry.day}_{entry.time_slot}_{entry.subject}_{entry.room}"
                    
                    if entry_id not in seen_entries:
                        seen_entries.add(entry_id)
                        timetable_entries.append(entry)
    
    # Get today's schedule
    from datetime import datetime
    today = datetime.now().strftime('%a').lower()
    today_schedule = []
    if current_teacher and timetable_entries:
        today_schedule = [entry for entry in timetable_entries if entry.day == today]
    
    # Calculate statistics for dashboard
    total_students = len(assigned_students)
    taught_subjects = Subject.objects.filter(teacher=current_teacher).count() if current_teacher else 0
    total_assignments = 0  # This can be implemented when assignment model is created
    attendance_rate = 95  # This can be calculated when attendance model is implemented
    
    # Calculate subject type counts
    core_subjects_count = 0
    elective_subjects_count = 0
    practical_subjects_count = 0
    
    if current_teacher:
        taught_subjects_list = Subject.objects.filter(teacher=current_teacher)
        core_subjects_count = taught_subjects_list.filter(subject_type='core').count()
        elective_subjects_count = taught_subjects_list.filter(subject_type='elective').count()
        practical_subjects_count = taught_subjects_list.filter(subject_type='practical').count()
    
    return render(request, 'teacher_dashboard.html', {
        'teacher': current_teacher,
        'teachers': teachers,
        'assigned_students': assigned_students,
        'timetable_entries': timetable_entries,
        'today_schedule': today_schedule,
        'total_students': total_students,
        'taught_subjects': taught_subjects,
        'total_assignments': total_assignments,
        'attendance_rate': attendance_rate,
        'core_subjects_count': core_subjects_count,
        'elective_subjects_count': elective_subjects_count,
        'practical_subjects_count': practical_subjects_count
    })




    if request.method == 'POST':

        first_name = request.POST.get('firstName')

        last_name = request.POST.get('lastName')

        email = request.POST.get('email')

        teacher_id = request.POST.get('teacherId')

        subject = request.POST.get('subjects')  # Using subjects from form

        years_of_experience = request.POST.get('experience')

        date_of_birth = request.POST.get('dob') if request.POST.get('dob') else '1990-01-01'

        # Use default teacher code as password
        teacher_code = "Teacher@123"

        teacher = Teacher.objects.create(
            first_name=first_name,

            last_name=last_name,

            email=email,

            teacher_id=teacher_id,

            teacher_code=teacher_code,

            subject=subject,

            years_of_experience=years_of_experience,

            date_of_birth=date_of_birth

        )

        return render(request, 'Teacher.html', {'success': True, 'teachers': Teacher.objects.all()})

    

    return render(request, 'Teacher.html', {'teachers': Teacher.objects.all()})








def change_student_password(request):
    """Handle student password change"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    student_email = request.session.get('student_email')
    if not student_email:
        return JsonResponse({'success': False, 'message': 'Student not logged in'})
    
    try:
        student = Student.objects.get(college_email=student_email, status__in=['approved', 'pending'])
        
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        
        # Validate current password
        if student.password and current_password != student.password:
            return JsonResponse({'success': False, 'message': 'Current password is incorrect'})
        elif not student.password and current_password != 'Student@123':
            return JsonResponse({'success': False, 'message': 'Current password is incorrect'})
        
        # Update password
        student.password = new_password
        student.save()
        
        return JsonResponse({'success': True, 'message': 'Password changed successfully'})
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error changing password'})

def logout_view(request):

    from django.shortcuts import redirect

    # Clear any session data if needed

    if hasattr(request, 'session'):

        request.session.flush()

    return redirect('index')



def student_details(request, student_id):

    """API endpoint to get student details for approval modal"""

    student = get_object_or_404(Student, id=student_id)

    

    student_data = {

        'id': student.id,

        'first_name': student.first_name,

        'last_name': student.last_name,

        'email': student.email,

        'mobile_no': student.mobile_no,

        'student_id': student.student_id if student.student_id else 'Pending ID Generation',

        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',

        'gender': student.get_gender_display() if student.gender else '',

        'student_image': student.student_image.url if student.student_image else None,

        'father_name': student.father_name,

        'father_occupation': student.father_occupation,

        'father_image': student.father_image.url if student.father_image else None,

        'mother_name': student.mother_name,

        'mother_occupation': student.mother_occupation,

        'mother_image': student.mother_image.url if student.mother_image else None,

        'hobby': student.hobby,

        'blood_group': student.blood_group,

        'aim_of_life': student.aim_of_life,

        'address': student.address,

        'course': student.course,

        'semester': student.semester,

        'batch': student.batch,

        'registration_date': student.registration_date.strftime('%Y-%m-%d %H:%M') if student.registration_date else '',

        'status': student.status,

        # Academic details

        'tenth_board': student.tenth_board,

        'tenth_percentage': float(student.tenth_percentage) if student.tenth_percentage else None,

        'tenth_year': student.tenth_year,

        'twelfth_board': student.twelfth_board,

        'twelfth_percentage': float(student.twelfth_percentage) if student.twelfth_percentage else None,

        'twelfth_year': student.twelfth_year,

        'diploma_course': student.diploma_course,

        'diploma_institution': student.diploma_institution,

        'diploma_percentage': float(student.diploma_percentage) if student.diploma_percentage else None,

        'diploma_year': student.diploma_year,

        'graduation_degree': student.graduation_degree,

        'graduation_university': student.graduation_university,

        'graduation_percentage': float(student.graduation_percentage) if student.graduation_percentage else None,

        'graduation_year': student.graduation_year,

        'graduation_status': student.graduation_status,

        'rejection_reason': student.rejection_reason

    }

    

    return JsonResponse({

        'success': True,

        'student': student_data

    })



def approve_student(request, student_id):

    """API endpoint to approve a student"""

    if request.method == 'POST':

        student = get_object_or_404(Student, id=student_id)

        

        try:

            # Update course, department, semester, and batch information if batch field contains batch ID or name
            if student.batch:
                try:
                    # First try to get batch by ID
                    from student.models import Batch
                    batch_obj = Batch.objects.get(id=int(student.batch))
                    student.course = batch_obj.course.course_name
                    student.department = batch_obj.department.name  # Add department info
                    
                    # Calculate current semester based on batch admission year and duration
                    from datetime import datetime
                    current_year = datetime.now().year
                    years_since_admission = current_year - batch_obj.admission_year
                    current_semester = min(years_since_admission * 2, batch_obj.duration * 2)
                    current_semester = max(1, current_semester)
                    
                    student.semester = str(current_semester)  # Set calculated current semester
                    student.batch = batch_obj.name  # Update batch field with batch name
                    
                    # Generate roll number and use it as student_id
                    admission_year_short = str(batch_obj.admission_year)[-2:]
                    dept_code = (batch_obj.department.code or 'GEN').upper()  # Ensure uppercase for consistency
                    existing_students_count = Student.objects.filter(
                        course=batch_obj.course.course_name,
                        batch__contains=str(batch_obj.admission_year)
                    ).count()
                    serial = str(existing_students_count + 1).zfill(2)
                    roll_number = f"{admission_year_short}-{dept_code}/{serial}"
                    student.student_id = roll_number  # Use roll number as student_id
                except (Batch.DoesNotExist, ValueError):
                    # If not found by ID, try to get by name
                    try:
                        batch_obj = Batch.objects.get(name=student.batch)
                        student.course = batch_obj.course.course_name
                        student.department = batch_obj.department.name  # Add department info
                        
                        # Calculate current semester based on batch admission year and duration
                        from datetime import datetime
                        current_year = datetime.now().year
                        years_since_admission = current_year - batch_obj.admission_year
                        current_semester = min(years_since_admission * 2, batch_obj.duration * 2)
                        current_semester = max(1, current_semester)
                        
                        student.semester = str(current_semester)  # Set calculated current semester
                        student.batch = batch_obj.name  # Update batch field with batch name
                        
                        # Generate roll number and use it as student_id
                        admission_year_short = str(batch_obj.admission_year)[-2:]
                        dept_code = (batch_obj.department.code or 'GEN').upper()  # Ensure uppercase
                        existing_students_count = Student.objects.filter(
                            course=batch_obj.course.course_name,
                            batch__contains=str(batch_obj.admission_year)
                        ).count()
                        serial = str(existing_students_count + 1).zfill(2)
                        roll_number = f"{admission_year_short}-{dept_code}/{serial}"
                        student.student_id = roll_number  # Use roll number as student_id
                    except Batch.DoesNotExist:
                        # Keep existing STU format if batch not found
                        if not student.student_id:
                            import random
                            import time
                            timestamp = int(time.time())
                            random_num = random.randint(1000, 9999)
                            student.student_id = f"STU{datetime.now().strftime('%Y%m%d')}{random_num}"
            else:
                # Generate STU format if no batch assigned
                if not student.student_id:
                    import random
                    import time
                    timestamp = int(time.time())
                    random_num = random.randint(1000, 9999)
                    student.student_id = f"STU{datetime.now().strftime('%Y%m%d')}{random_num}"
            
            student.status = 'approved'

            student.rejection_reason = None  # Clear any previous rejection reason

            student.save()

            # Send approval email to student
            email_sent = send_student_approval_email(student)
            email_status = " and approval email sent" if email_sent else " but email failed to send"

            

            return JsonResponse({

                'success': True,

                'message': f'Student {student.first_name} {student.last_name} has been approved with ID: {student.student_id}{email_status}.',

                'student_id': student.student_id

            })

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error approving student: {str(e)}'

            })

    

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def reject_student(request, student_id):

    """API endpoint to reject a student"""

    if request.method == 'POST':

        student = get_object_or_404(Student, id=student_id)

        

        # Get rejection reason from request body

        try:

            data = json.loads(request.body)

            rejection_reason = data.get('rejection_reason', '')

        except:

            rejection_reason = ''

        

        student.status = 'rejected'

        student.rejection_reason = rejection_reason

        student.save()

        

        return JsonResponse({

            'success': True,

            'message': f'Student {student.first_name} {student.last_name} has been rejected.'

        })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def delete_student(request, student_id):
    """API endpoint to delete a student"""
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        
        try:
            student_name = f"{student.first_name} {student.last_name}"
            student.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Student {student_name} has been deleted successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting student: {str(e)}'
            })
    
    # If GET request, return error
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })



def update_student(request, student_id):
    """API endpoint to update a student"""
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        
        try:
            # Get form data
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            email = request.POST.get('email')
            mobile_no = request.POST.get('mobileNo')
            date_of_birth = request.POST.get('dateOfBirth')
            gender = request.POST.get('gender')
            course = request.POST.get('course')
            department = request.POST.get('department')
            semester = request.POST.get('semester')
            batch = request.POST.get('batch')
            hobby = request.POST.get('hobby')
            blood_group = request.POST.get('bloodGroup')
            aim_of_life = request.POST.get('aimOfLife')
            address = request.POST.get('address')
            
            # Academic details
            tenth_board = request.POST.get('tenthBoard')
            tenth_percentage = request.POST.get('tenthPercentage')
            tenth_year = request.POST.get('tenthYear')
            twelfth_board = request.POST.get('twelfthBoard')
            twelfth_percentage = request.POST.get('twelfthPercentage')
            twelfth_year = request.POST.get('twelfthYear')
            diploma_course = request.POST.get('diplomaCourse')
            diploma_institution = request.POST.get('diplomaInstitution')
            diploma_percentage = request.POST.get('diplomaPercentage')
            diploma_year = request.POST.get('diplomaYear')
            graduation_degree = request.POST.get('graduationDegree')
            graduation_university = request.POST.get('graduationUniversity')
            graduation_percentage = request.POST.get('graduationPercentage')
            graduation_year = request.POST.get('graduationYear')
            graduation_status = request.POST.get('graduationStatus')
            
            # Handle file uploads
            student_image = request.FILES.get('studentImage')
            father_image = request.FILES.get('fatherImage')
            mother_image = request.FILES.get('motherImage')
            
            # Update only the fields that are actually provided
            if first_name and first_name.strip():
                student.first_name = first_name
            if last_name and last_name.strip():
                student.last_name = last_name
            if email and email.strip():
                student.email = email
            if mobile_no and mobile_no.strip():
                student.mobile_no = mobile_no
            if date_of_birth:
                student.date_of_birth = date_of_birth
            if gender and gender.strip():
                student.gender = gender
            if course and course.strip():
                student.course = course
            if semester and semester.strip():
                student.semester = semester
            if batch and batch.strip():
                student.batch = batch
            if hobby and hobby.strip():
                student.hobby = hobby
            if blood_group and blood_group.strip():
                student.blood_group = blood_group
            if aim_of_life and aim_of_life.strip():
                student.aim_of_life = aim_of_life
            if address and address.strip():
                student.address = address
            
            # Update academic fields only if provided
            if tenth_board and tenth_board.strip():
                student.tenth_board = tenth_board
            if tenth_percentage and tenth_percentage.strip():
                student.tenth_percentage = float(tenth_percentage)
            if tenth_year and tenth_year.strip():
                student.tenth_year = int(tenth_year)
            if twelfth_board and twelfth_board.strip():
                student.twelfth_board = twelfth_board
            if twelfth_percentage and twelfth_percentage.strip():
                student.twelfth_percentage = float(twelfth_percentage)
            if twelfth_year and twelfth_year.strip():
                student.twelfth_year = int(twelfth_year)
            if diploma_course and diploma_course.strip():
                student.diploma_course = diploma_course
            if diploma_institution and diploma_institution.strip():
                student.diploma_institution = diploma_institution
            if diploma_percentage and diploma_percentage.strip():
                student.diploma_percentage = float(diploma_percentage)
            if diploma_year and diploma_year.strip():
                student.diploma_year = int(diploma_year)
            if graduation_degree and graduation_degree.strip():
                student.graduation_degree = graduation_degree
            if graduation_university and graduation_university.strip():
                student.graduation_university = graduation_university
            if graduation_percentage and graduation_percentage.strip():
                student.graduation_percentage = float(graduation_percentage)
            if graduation_year and graduation_year.strip():
                student.graduation_year = int(graduation_year)
            if graduation_status and graduation_status.strip():
                student.graduation_status = graduation_status
            
            # Handle image updates
            if student_image:
                student.student_image = student_image
            if father_image:
                student.father_image = father_image
            if mother_image:
                student.mother_image = mother_image
            
            student.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Student {first_name} {last_name} has been updated successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating student: {str(e)}'
            })
    
    # If GET request, return student data for editing
    student = get_object_or_404(Student, id=student_id)
    
    student_data = {
        'id': student.id,
        'first_name': student.first_name,
        'last_name': student.last_name,
        'email': student.email,
        'mobile_no': student.mobile_no,
        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
        'gender': student.gender,
        'course': student.course,
        'semester': student.semester,
        'batch': student.batch,
        'hobby': student.hobby,
        'blood_group': student.blood_group,
        'aim_of_life': student.aim_of_life,
        'address': student.address,
        'student_image': student.student_image.url if student.student_image else None,
        'father_name': student.father_name,
        'father_occupation': student.father_occupation,
        'father_image': student.father_image.url if student.father_image else None,
        'mother_name': student.mother_name,
        'mother_occupation': student.mother_occupation,
        'mother_image': student.mother_image.url if student.mother_image else None,
        'tenth_board': student.tenth_board,
        'tenth_percentage': float(student.tenth_percentage) if student.tenth_percentage else None,
        'tenth_year': student.tenth_year,
        'twelfth_board': student.twelfth_board,
        'twelfth_percentage': float(student.twelfth_percentage) if student.twelfth_percentage else None,
        'twelfth_year': student.twelfth_year,
        'diploma_course': student.diploma_course,
        'diploma_institution': student.diploma_institution,
        'diploma_percentage': float(student.diploma_percentage) if student.diploma_percentage else None,
        'diploma_year': student.diploma_year,
        'graduation_degree': student.graduation_degree,
        'graduation_university': student.graduation_university,
        'graduation_percentage': float(student.graduation_percentage) if student.graduation_percentage else None,
        'graduation_year': student.graduation_year,
        'graduation_status': student.graduation_status,
    }
    
    return JsonResponse({
        'success': True,
        'student': student_data
    })



# Session Management Views

def add_session(request):

    """API endpoint to create a new session"""

    if request.method == 'POST':

        start_date = request.POST.get('startDate')

        end_date = request.POST.get('endDate')

        description = request.POST.get('description', '')

        

        try:

            # Validate dates

            if start_date >= end_date:

                return JsonResponse({

                    'success': False,

                    'message': 'Start date must be before end date'

                })

            

            # Auto-generate session name from dates

            start_year = start_date.split('-')[0]

            end_year = end_date.split('-')[0]

            session_name = f"{start_year}-{end_year} Academic Session"

            

            # Check if session name already exists, add suffix if needed

            counter = 1

            original_session_name = session_name

            while Session.objects.filter(session_name=session_name).exists():

                session_name = f"{original_session_name} ({counter})"

                counter += 1

            

            # Set default status to 'upcoming'

            status = 'upcoming'

            

            session = Session.objects.create(

                session_name=session_name,

                start_date=start_date,

                end_date=end_date,

                status=status,

                description=description

            )

            

            return JsonResponse({

                'success': True,

                'message': f'Session "{session_name}" created successfully!',

                'session_id': session.id

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error creating session: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def get_sessions(request):

    """API endpoint to get all sessions for management table"""

    if request.method == 'GET':

        sessions = Session.objects.all().order_by('-created_at')

        

        sessions_data = []

        for session in sessions:

            sessions_data.append({

                'id': session.id,

                'session_name': session.session_name,

                'start_date': session.start_date.strftime('%Y-%m-%d'),

                'end_date': session.end_date.strftime('%Y-%m-%d'),

                'status': session.status,

                'status_display': session.get_status_display(),

                'description': session.description,

                'created_at': session.created_at.strftime('%Y-%m-%d %H:%M')

            })

        

        return JsonResponse({

            'success': True,

            'sessions': sessions_data

        })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def update_session_status(request, session_id):

    """API endpoint to update session status"""

    if request.method == 'POST':

        try:

            data = json.loads(request.body)

            new_status = data.get('status')

            

            session = get_object_or_404(Session, id=session_id)

            

            # If setting as active, deactivate other active sessions

            if new_status == 'active':

                Session.objects.filter(status='active').update(status='completed')

            

            session.status = new_status

            session.save()

            

            return JsonResponse({

                'success': True,

                'message': f'Session "{session.session_name}" status updated to {new_status}'

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error updating session: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def delete_session(request, session_id):

    """API endpoint to delete a session"""

    if request.method == 'POST':

        try:

            session = get_object_or_404(Session, id=session_id)

            session_name = session.session_name

            session.delete()

            

            return JsonResponse({

                'success': True,

                'message': f'Session "{session_name}" deleted successfully'

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error deleting session: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



# Subject Assignment Views

def get_department_semesters(request, department_id):
    """API endpoint to get semesters for a department"""
    if request.method == 'GET':
        try:
            # For now, return standard semesters (1-8)
            # In a real implementation, this would be based on department courses
            semesters = []
            for i in range(1, 9):  # 8 semesters
                semesters.append({
                    'id': i,
                    'semester_number': i
                })
            
            return JsonResponse({
                'success': True,
                'semesters': semesters
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error loading semesters: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_semester_subjects(request, department_id, semester_id):
    """API endpoint to get subjects for a department and semester"""
    if request.method == 'GET':
        try:
            # Get subjects that are active and belong to the selected department and semester
            semester_subjects = Subject.objects.filter(
                is_active=True,
                department_id=department_id,
                semester=semester_id
            ).order_by('subject_code')
            
            # If no semester-specific subjects found, get all department subjects
            if not semester_subjects.exists():
                semester_subjects = Subject.objects.filter(
                    is_active=True,
                    department_id=department_id
                ).order_by('subject_code')
            
            # Add common subjects for 1st and 2nd semester
            common_subjects = []
            if semester_id in [1, 2]:  # 1st and 2nd semester
                # Define common subjects that should appear for all departments
                common_subject_names = [
                    'Mathematics', 'Physics', 'Chemistry', 
                    'English', 'Environmental Science', 'Basic Electronics'
                ]
                
                for subject_name in common_subject_names:
                    try:
                        common_subject = Subject.objects.get(
                            subject_name=subject_name,
                            is_active=True
                        )
                        common_subjects.append({
                            'id': common_subject.id,
                            'subject_code': common_subject.subject_code,
                            'subject_name': common_subject.subject_name,
                            'subject_type': common_subject.subject_type,
                            'credits': common_subject.credits
                        })
                    except Subject.DoesNotExist:
                        pass  # Skip if subject doesn't exist
            
            # Convert semester subjects to data format
            subjects_data = []
            for subject in semester_subjects:
                subjects_data.append({
                    'id': subject.id,
                    'subject_code': subject.subject_code,
                    'subject_name': subject.subject_name,
                    'subject_type': subject.subject_type,
                    'credits': subject.credits
                })
            
            # Combine department subjects and common subjects
            all_subjects = subjects_data + common_subjects
            
            # Remove duplicates based on subject name
            seen_names = set()
            unique_subjects = []
            for subject in all_subjects:
                if subject['subject_name'] not in seen_names:
                    seen_names.add(subject['subject_name'])
                    unique_subjects.append(subject)
            
            # Sort by subject code
            unique_subjects.sort(key=lambda x: x['subject_code'])
            
            return JsonResponse({
                'success': True,
                'subjects': unique_subjects
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error loading subjects: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_subject_teachers(request, subject_id):
    """API endpoint to get teachers available for a subject"""
    if request.method == 'GET':
        try:
            # Get all teachers (in a real implementation, this might filter by subject specialization)
            teachers = Teacher.objects.all().order_by('first_name', 'last_name')
            
            teachers_data = []
            for teacher in teachers:
                teachers_data.append({
                    'id': teacher.id,
                    'first_name': teacher.first_name,
                    'last_name': teacher.last_name,
                    'teacher_id': teacher.teacher_id,
                    'department': teacher.department.name if teacher.department else None
                })
            
            return JsonResponse({
                'success': True,
                'teachers': teachers_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error loading teachers: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_department_teachers(request, department_id):
    """API endpoint to get teachers for a specific department"""
    if request.method == 'GET':
        try:
            # Get teachers belonging to the selected department
            teachers = Teacher.objects.filter(department_id=department_id).order_by('first_name', 'last_name')
            
            # Debug: Log the department and teacher count
            print(f"Department ID: {department_id}")
            print(f"Found {teachers.count()} teachers in this department")
            
            # If no teachers found in this department, get all teachers as fallback
            if teachers.count() == 0:
                print("No teachers found in this department, showing all teachers as fallback")
                teachers = Teacher.objects.all().order_by('first_name', 'last_name')
                print(f"Fallback: Found {teachers.count()} total teachers")
            
            teachers_data = []
            for teacher in teachers:
                teachers_data.append({
                    'id': teacher.id,
                    'first_name': teacher.first_name,
                    'last_name': teacher.last_name,
                    'teacher_id': teacher.teacher_id,
                    'department': teacher.department.name if teacher.department else None
                })
                print(f"Teacher: {teacher.first_name} {teacher.last_name} - Dept: {teacher.department.name if teacher.department else 'None'}")
            
            return JsonResponse({
                'success': True,
                'teachers': teachers_data
            })
        except Exception as e:
            print(f"Error in get_department_teachers: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error loading teachers: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_subject_assignments(request):
    """API endpoint to get all current subject assignments"""
    if request.method == 'GET':
        try:
            # Get all subjects with assigned teachers
            assignments = Subject.objects.filter(
                teacher__isnull=False,
                is_active=True
            ).select_related('teacher', 'department', 'course').order_by('department__name', 'subject_code')
            
            assignments_data = []
            for subject in assignments:
                assignments_data.append({
                    'id': subject.id,
                    'teacher_name': f"{subject.teacher.first_name} {subject.teacher.last_name}",
                    'teacher_id': subject.teacher.teacher_id,
                    'subject_code': subject.subject_code,
                    'subject_name': subject.subject_name,
                    'subject_type': subject.subject_type,
                    'department_name': subject.department.name if subject.department else 'No Department',
                    'course_name': subject.course.course_name if subject.course else 'No Course',
                    'credits': subject.credits
                })
            
            return JsonResponse({
                'success': True,
                'assignments': assignments_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error loading assignments: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def remove_subject_assignment(request, assignment_id):
    """API endpoint to remove a subject assignment"""
    if request.method == 'POST':
        try:
            subject = Subject.objects.get(id=assignment_id)
            subject.teacher = None
            subject.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Assignment removed successfully for "{subject.subject_name}"'
            })
        except Subject.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Subject not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error removing assignment: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def assign_subject(request):
    """API endpoint to assign a subject to a teacher"""
    if request.method == 'POST':
        try:
            department_id = request.POST.get('department')
            semester_id = request.POST.get('semester')
            subject_id = request.POST.get('subject')
            teacher_id = request.POST.get('teacher')
            
            # Validate required fields
            if not all([department_id, semester_id, subject_id, teacher_id]):
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            # Get the objects
            try:
                department = Department.objects.get(id=department_id)
                subject = Subject.objects.get(id=subject_id)
                teacher = Teacher.objects.get(id=teacher_id)
            except (Department.DoesNotExist, Subject.DoesNotExist, Teacher.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid selection. Please check your inputs.'
                })
            
            # Update the subject with the assigned teacher
            subject.teacher = teacher
            subject.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Subject "{subject.subject_name}" successfully assigned to {teacher.first_name} {teacher.last_name}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error assigning subject: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def add_subject(request):

    """API endpoint to create a new subject"""

    if request.method == 'POST':

        # Handle both JSON and form data
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            subject_name = data.get('subject_name')
            subject_code = data.get('subject_code')
            course_id = data.get('course')
            department_id = data.get('department')
            semester = data.get('semester')
            teacher_id = data.get('teacher')
            is_active = data.get('isActive', True)
        else:
            subject_name = request.POST.get('subjectName')
            subject_code = request.POST.get('subjectCode')
            course_id = request.POST.get('course')
            department_id = request.POST.get('department')
            semester = request.POST.get('semester')
            teacher_id = request.POST.get('teacher')
            is_active = request.POST.get('isActive') == 'on'

        

        try:

            # Generate subject code automatically based on department and subject name
            subject_code = generate_subject_code(subject_name, department_id, course_id, semester)

            
            # Get course, department, and teacher objects
            course = Course.objects.get(id=course_id) if course_id else None
            department = Department.objects.get(id=department_id) if department_id else None
            teacher = Teacher.objects.get(id=teacher_id) if teacher_id else None

            
            subject = Subject.objects.create(
                subject_code=subject_code,
                subject_name=subject_name,
                course=course,
                department=department,
                teacher=teacher,
                semester=semester if semester else 1,
                is_active=is_active
            )

            

            return JsonResponse({

                'success': True,

                'message': f'Subject "{subject_name}" created successfully!',

                'subject_id': subject.id

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error creating subject: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def get_courses_for_dropdown(request):

    """API endpoint to get all active courses for dropdown"""

    if request.method == 'GET':

        courses = Course.objects.filter(is_active=True).order_by('course_name')

        

        courses_data = []

        for course in courses:

            courses_data.append({

                'id': course.id,

                'course_name': course.course_name,

                'duration': course.duration

            })

        

        return JsonResponse({

            'success': True,

            'courses': courses_data

        })

    

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })

def get_teachers_for_dropdown(request):
    """API endpoint to get all teachers for dropdown"""
    if request.method == 'GET':
        teachers = Teacher.objects.all().order_by('first_name', 'last_name')
        
        teachers_data = []
        for teacher in teachers:
            teachers_data.append({
                'id': teacher.id,
                'name': f"{teacher.first_name} {teacher.last_name}",
                'department': teacher.department.name if teacher.department else None
            })
        
        return JsonResponse({
            'success': True,
            'teachers': teachers_data
        })
    
    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def get_subjects(request):

    """API endpoint to get all subjects for management table"""

    if request.method == 'GET':

        # Get department_id parameter for filtering
        department_id = request.GET.get('department_id')
        
        if department_id:
            subjects = Subject.objects.filter(department_id=department_id).order_by('subject_code')
        else:
            subjects = Subject.objects.all().order_by('subject_code')

        

        subjects_data = []

        for subject in subjects:

            subjects_data.append({

                'id': subject.id,

                'subject_code': subject.subject_code,

                'subject_name': subject.subject_name,

                'type': subject.subject_type,  # Changed from 'subject_type' to 'type'

                'credits': subject.credits,

                'semester': subject.semester,

                'department': subject.department.name if subject.department else 'No Department',

                'description': subject.description,

                'course': subject.course.course_name if subject.course else None,

                'teacher': f"{subject.teacher.first_name} {subject.teacher.last_name}" if subject.teacher else None,

                'is_active': subject.is_active,

                'status_display': 'Active' if subject.is_active else 'Inactive',

                'created_at': subject.created_at.strftime('%Y-%m-%d %H:%M')

            })

        

        return JsonResponse({

            'success': True,

            'subjects': subjects_data

        })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def update_subject_status(request, subject_id):

    """API endpoint to update subject active status"""

    if request.method == 'POST':

        try:

            data = json.loads(request.body)

            is_active = data.get('is_active')

            

            subject = get_object_or_404(Subject, id=subject_id)

            subject.is_active = is_active

            subject.save()

            

            status_text = 'activated' if is_active else 'deactivated'

            return JsonResponse({

                'success': True,

                'message': f'Subject "{subject.subject_name}" {status_text} successfully'

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error updating subject: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def delete_subject(request, subject_id):

    """API endpoint to delete a subject"""

    if request.method == 'POST':

        try:

            subject = get_object_or_404(Subject, id=subject_id)

            subject_name = subject.subject_name

            subject.delete()

            

            return JsonResponse({

                'success': True,

                'message': f'Subject "{subject_name}" deleted successfully'

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error deleting subject: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



# Teacher Management Views

def add_teacher(request):

    """API endpoint to create a new teacher"""

    if request.method == 'POST':

        first_name = request.POST.get('firstName')

        last_name = request.POST.get('lastName')

        email = request.POST.get('email')

        # Auto-generate teacher code instead of getting from form
        teacher_code = f"TC{datetime.now().strftime('%Y%m%d')}{str(Teacher.objects.count() + 1).zfill(3)}"

        department_id = request.POST.get('department')

        years_of_experience = request.POST.get('yearsOfExperience')

        date_of_birth = request.POST.get('dateOfBirth')

        

        try:

            # Validate years of experience

            years_of_experience = int(years_of_experience) if years_of_experience else 0

            

            # Check if email already exists

            if Teacher.objects.filter(email=email).exists():

                return JsonResponse({

                    'success': False,

                    'message': 'Email already exists'

                })

            

            # Check if teacher code already exists

            if Teacher.objects.filter(teacher_code=teacher_code).exists():

                return JsonResponse({

                    'success': False,

                    'message': 'Teacher code already exists'

                })

            

            # Get department object
            department = None
            if department_id:
                try:
                    department = Department.objects.get(id=department_id)
                except Department.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Selected department does not exist'
                    })

            

            # Auto-generate teacher ID if not provided

            teacher_id = f"TCH-{datetime.now().strftime('%Y%m%d')}{str(Teacher.objects.count() + 1).zfill(3)}"

            

            teacher = Teacher.objects.create(

                first_name=first_name,

                last_name=last_name,

                email=email,

                teacher_id=teacher_id,

                teacher_code=teacher_code,

                department=department,

                years_of_experience=years_of_experience,

                date_of_birth=date_of_birth

            )

            
            # Send welcome email to teacher
            try:
                email_sent = send_teacher_welcome_email(teacher)
                if email_sent:
                    print(f"Welcome email sent to teacher: {teacher.email}")
                else:
                    print(f"Failed to send welcome email to teacher: {teacher.email}")
            except Exception as e:
                print(f"Error sending teacher email: {e}")
            

            return JsonResponse({

                'success': True,

                'message': f'Teacher "{first_name} {last_name}" added successfully! Teacher Code: {teacher_code}. Welcome email sent to {teacher.email}.',

                'teacher_id': teacher.id,

                'teacher_code': teacher_code

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error adding teacher: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def get_teachers(request):

    """API endpoint to get all teachers for management table"""

    if request.method == 'GET':

        teachers = Teacher.objects.all().order_by('first_name', 'last_name')

        print(f"Found {teachers.count()} teachers")

        teachers_data = []

        for teacher in teachers:

            print(f"Processing teacher: {teacher.first_name} {teacher.last_name}, department: {teacher.department}")

            teachers_data.append({

                'id': teacher.id,

                'teacher_id': teacher.teacher_id,

                'first_name': teacher.first_name,

                'last_name': teacher.last_name,

                'full_name': f"{teacher.first_name} {teacher.last_name}",

                'email': teacher.email,

                'department': teacher.department.name if teacher.department else 'Not assigned',

                'years_of_experience': teacher.years_of_experience,

                'date_of_birth': teacher.date_of_birth.strftime('%Y-%m-%d') if teacher.date_of_birth else '',

                'hire_date': teacher.hire_date.strftime('%Y-%m-%d') if teacher.hire_date else ''

            })

        

        return JsonResponse({

            'success': True,

            'teachers': teachers_data

        })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def delete_teacher(request, teacher_id):

    """API endpoint to delete a teacher"""

    if request.method == 'POST':

        try:

            teacher = get_object_or_404(Teacher, id=teacher_id)

            teacher_name = f"{teacher.first_name} {teacher.last_name}"

            teacher.delete()

            

            return JsonResponse({

                'success': True,

                'message': f'Teacher "{teacher_name}" deleted successfully'

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error deleting teacher: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



# Course Management Views

def add_course(request):

    """API endpoint to create a new course"""

    if request.method == 'POST':

        course_name = request.POST.get('courseName')

        status = request.POST.get('status') == 'active'

        

        try:

            # Check if course name already exists

            if Course.objects.filter(course_name=course_name).exists():

                return JsonResponse({

                    'success': False,

                    'message': 'Course name already exists'

                })

            

            course = Course.objects.create(

                course_name=course_name,

                is_active=status

            )

            

            return JsonResponse({

                'success': True,

                'message': f'Course "{course_name}" added successfully!',

                'course_id': course.id

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error adding course: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def get_courses(request):

    """API endpoint to get all courses for management table"""

    if request.method == 'GET':

        courses = Course.objects.all().order_by('course_name')

        

        courses_data = []

        for course in courses:

            courses_data.append({

                'id': course.id,

                'course_name': course.course_name,

                'is_active': course.is_active,

                'status_display': 'Active' if course.is_active else 'Inactive',

                'created_at': course.created_at.strftime('%Y-%m-%d %H:%M')

            })

        

        return JsonResponse({

            'success': True,

            'courses': courses_data

        })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def update_course_status(request, course_id):

    """API endpoint to update course active status"""

    if request.method == 'POST':

        try:

            data = json.loads(request.body)

            is_active = data.get('is_active')

            

            course = get_object_or_404(Course, id=course_id)

            course.is_active = is_active

            course.save()

            

            status_text = 'activated' if is_active else 'deactivated'

            return JsonResponse({

                'success': True,

                'message': f'Course "{course.course_name}" {status_text} successfully'

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error updating course: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })



def delete_course(request, course_id):

    """API endpoint to delete a course"""

    if request.method == 'POST':

        try:

            course = get_object_or_404(Course, id=course_id)

            course_name = course.course_name

            course.delete()

            

            return JsonResponse({

                'success': True,

                'message': f'Course "{course_name}" deleted successfully'

            })

            

        except Exception as e:

            return JsonResponse({

                'success': False,

                'message': f'Error deleting course: {str(e)}'

            })

    

    # If GET request, return error

    return JsonResponse({

        'success': False,

        'message': 'Invalid request method'

    })




# Department Management Views
def add_department(request):
    """API endpoint to create a new department"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('departmentName', '').strip()
            code = request.POST.get('departmentCode', '').strip()
            
            # Validate required fields
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'Department name is required'
                })
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'message': 'Department code is required'
                })
            
            # Check if department already exists
            if Department.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Department with this name already exists'
                })
            
            # Check if department code already exists
            if Department.objects.filter(code__iexact=code).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Department with this code already exists'
                })
            
            # Create new department
            department = Department.objects.create(
                name=name,
                code=code,
                head=None  # Can be added later if needed
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Department "{department.name}" added successfully',
                'department': {
                    'id': department.id,
                    'name': department.name,
                    'code': department.code,
                    'head': department.head,
                    'created_at': department.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error adding department: {str(e)}'
            })
    
    # If GET request, return error
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


def get_departments(request):
    """API endpoint to get all departments for management table"""
    if request.method == 'GET':
        departments = Department.objects.all().order_by('name')
        
        departments_data = []
        for department in departments:
            departments_data.append({
                'id': department.id,
                'name': department.name,
                'head': department.head or 'Not assigned',
                'created_at': department.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': department.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'departments': departments_data
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


def delete_department(request, department_id):
    """API endpoint to delete a department"""
    if request.method == 'POST':
        try:
            department = get_object_or_404(Department, id=department_id)
            department_name = department.name
            department.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Department "{department_name}" deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting department: {str(e)}'
            })
    
    # If GET request, return error
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


# Payment Management Views
def get_payments(request):
    """API endpoint to get all payments data with filtering support"""
    if request.method == 'GET':
        try:
            # Get filter parameters
            batch_filter = request.GET.get('batch', '')
            status_filter = request.GET.get('status', '')
            year_filter = request.GET.get('year', '')
            search_filter = request.GET.get('search', '')
            date_filter = request.GET.get('date', '')
            
            # Get all students with their batches
            students = Student.objects.filter(status='approved')
            
            # Apply filters
            if batch_filter:
                # Try to filter by batch ID first, then by batch name
                try:
                    batch_id = int(batch_filter)
                    # Get batch name by ID
                    batch_obj = Batch.objects.get(id=batch_id)
                    batch_filter_name = batch_obj.name
                    print(f"Filtering by batch ID {batch_id}, batch name: {batch_filter_name}")
                except (ValueError, Batch.DoesNotExist):
                    # If not an ID or batch not found, use as batch name directly
                    batch_filter_name = batch_filter
                    print(f"Filtering by batch name: {batch_filter_name}")
                
                # Filter students by the batch name
                students = students.filter(batch=batch_filter_name)
                print(f"Students after batch filter: {students.count()}")
            
            if search_filter:
                students = students.filter(
                    Q(first_name__icontains=search_filter) |
                    Q(last_name__icontains=search_filter) |
                    Q(email__icontains=search_filter) |
                    Q(student_id__icontains=search_filter)
                )
            
            payments_data = []
            total_students = 0
            total_collected = 0.0
            total_due = 0.0
            pending_payments = 0
            
            # Debug: Log available batches
            batches = Batch.objects.all()
            print(f"Available batches: {list(batches.values('id', 'name', 'total_course_fee', 'payment_type', 'number_of_installments'))}")
            
            # Debug: Log a few sample students and their batch values
            sample_students = students[:5] if students.count() > 0 else []
            print(f"Sample students: {list(sample_students.values('id', 'first_name', 'last_name', 'batch'))}")
            
            for student in students:
                # Get batch information by matching batch name
                batch = None
                if student.batch:
                    batches = Batch.objects.filter(name=student.batch)
                    if batches.exists():
                        # Prefer batches with non-zero fees if multiple batches exist
                        batch = batches.filter(total_course_fee__gt=0).first()
                        if not batch:
                            batch = batches.first()  # Fallback to first batch if none have fees
                
                if not batch:
                    print(f"No batch found for student {student.student_id} with batch name '{student.batch}'")
                    continue
                
                # Apply year filter
                if year_filter:
                    if not batch.admission_year or int(year_filter) < batch.admission_year or int(year_filter) > (batch.admission_year + (batch.course.duration or 4)):
                        continue
                
                total_students += 1
                
                # Calculate payment information
                annual_fee = float(batch.total_course_fee or 0)
                course_duration = batch.course.duration or 4
                total_fee = annual_fee * course_duration  # Convert annual fee to total course fee
                
                # Get actual payment records for this student
                student_payments = Payment.objects.filter(student=student, status='completed')
                
                # Apply date filter if provided
                if date_filter:
                    try:
                        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                        student_payments = student_payments.filter(payment_date__date=filter_date)
                    except ValueError:
                        pass  # Invalid date format, ignore date filter
                
                paid_amount = float(sum(payment.amount for payment in student_payments))
                due_amount = total_fee - paid_amount
                
                # Determine payment status
                if due_amount <= 0:
                    status = 'paid'
                elif paid_amount > 0:
                    status = 'partial'
                    pending_payments += 1
                else:
                    status = 'due'
                    pending_payments += 1
                
                # Apply status filter
                if status_filter and status != status_filter:
                    continue
                
                total_collected += paid_amount
                total_due += due_amount
                
                print(f"Student: {student.first_name} {student.last_name}, Batch: {batch.name}, Total Fee: {total_fee}")
                
                payments_data.append({
                    'id': student.id,
                    'student_name': f"{student.first_name} {student.last_name}",
                    'student_id': student.student_id or f"STU{student.id:06d}",
                    'student_email': student.email,
                    'batch_name': batch.name,
                    'course_name': batch.course.course_name,
                    'department_name': batch.department.name,
                    'total_fee': total_fee,
                    'paid_amount': paid_amount,
                    'due_amount': due_amount,
                    'status': status,
                    'payment_type': batch.payment_type,
                    'payment_type_display': batch.get_payment_type_display(),
                    'number_of_installments': batch.number_of_installments,
                    'admission_year': batch.admission_year,
                    'course_duration': batch.course.duration or 4
                })
            
            # Get all batches for filter
            batches = Batch.objects.all().order_by('-admission_year', 'name')
            batches_data = [{'id': batch.id, 'name': batch.name, 'admission_year': batch.admission_year} for batch in batches]
            
            print(f"Batches data being returned: {batches_data}")
            print(f"Number of batches: {len(batches_data)}")
            
            statistics = {
                'total_students': total_students,
                'total_collected': total_collected,
                'total_due': total_due,
                'pending_payments': pending_payments
            }
            
            print(f"Returning {len(payments_data)} payment records")
            
            return JsonResponse({
                'success': True,
                'payments': payments_data,
                'statistics': statistics,
                'batches': batches_data
            })
            
        except Exception as e:
            print(f"Error in get_payments: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error loading payments: {str(e)}'
            })

def get_payment_details(request, payment_id):
    """API endpoint to get detailed payment information for a student"""
    if request.method == 'GET':
        try:
            student = get_object_or_404(Student, id=payment_id)
            
            # Get batch information by matching batch name
            batch = None
            if student.batch:
                batches = Batch.objects.filter(name=student.batch)
                if batches.exists():
                    # Prefer batches with non-zero fees if multiple batches exist
                    batch = batches.filter(total_course_fee__gt=0).first()
                    if not batch:
                        batch = batches.first()  # Fallback to first batch if none have fees
            
            if not batch:
                return JsonResponse({
                    'success': False,
                    'message': 'Student is not assigned to any batch'
                })
            
            # Calculate payment information
            annual_fee = float(batch.total_course_fee or 0)
            course_duration = batch.course.duration or 4
            total_fee = annual_fee * course_duration  # Convert annual fee to total course fee
            
            # Get actual payment records for this student
            student_payments = Payment.objects.filter(student=student, status='completed')
            paid_amount = float(sum(payment.amount for payment in student_payments))
            due_amount = total_fee - paid_amount
            
            # Determine payment status
            if due_amount <= 0:
                status = 'paid'
            elif paid_amount > 0:
                status = 'partial'
            else:
                status = 'due'
            
            payment_data = {
                'id': student.id,
                'student_name': f"{student.first_name} {student.last_name}",
                'student_id': student.student_id or f"STU{student.id:06d}",
                'student_email': student.email,
                'batch_name': batch.name,
                'course_name': batch.course.course_name,
                'department_name': batch.department.name,
                'total_fee': total_fee,
                'paid_amount': paid_amount,
                'due_amount': due_amount,
                'status': status,
                'payment_type': batch.payment_type,
                'payment_type_display': batch.get_payment_type_display(),
                'number_of_installments': batch.number_of_installments,
                'admission_year': batch.admission_year,
                'semester': student.semester or '1',
                'course_duration': batch.course.duration
            }
            
            return JsonResponse({
                'success': True,
                'payment': payment_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error loading payment details: {str(e)}'
            })

def get_payment_history(request, payment_id):
    """API endpoint to get payment history for a student"""
    if request.method == 'GET':
        try:
            student = get_object_or_404(Student, id=payment_id)
            
            # Get actual payment history for this student
            payments = Payment.objects.filter(student=student).order_by('-payment_date')
            history_data = []
            
            for payment in payments:
                history_data.append({
                    'id': payment.id,
                    'amount': float(payment.amount),
                    'payment_date': payment.payment_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_mode': payment.payment_mode,
                    'payment_mode_display': payment.get_payment_mode_display(),
                    'transaction_id': payment.transaction_id,
                    'description': payment.description,
                    'status': payment.status,
                    'status_display': payment.get_status_display(),
                    'installment_number': payment.installment_number
                })
            
            return JsonResponse({
                'success': True,
                'history': history_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error loading payment history: {str(e)}'
            })

def record_payment(request):
    """API endpoint to record a new payment for a student"""
    if request.method == 'POST':
        try:
            # Get form data
            student_id = request.POST.get('student_id')
            amount = request.POST.get('amount')
            payment_mode = request.POST.get('payment_mode')
            transaction_id = request.POST.get('transaction_id', '')
            description = request.POST.get('description', '')
            installment_number = request.POST.get('installment_number', '')
            
            # Validate required fields
            if not student_id or not amount or not payment_mode:
                return JsonResponse({
                    'success': False,
                    'message': 'Student ID, amount, and payment mode are required'
                })
            
            # Get student
            student = get_object_or_404(Student, id=student_id)
            
            # Create payment record
            payment = Payment.objects.create(
                student=student,
                amount=amount,
                payment_mode=payment_mode,
                transaction_id=transaction_id if transaction_id else None,
                description=description if description else None,
                installment_number=int(installment_number) if installment_number else None,
                status='completed'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Payment recorded successfully',
                'payment_id': payment.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error recording payment: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

# Batch Management Views
def add_batch(request):
    """API endpoint to create a new batch"""
    if request.method == 'POST':
        try:
            # Get form data
            course_id = request.POST.get('courseSelect', '').strip()
            department_id = request.POST.get('departmentSelect', '').strip()
            admission_year = request.POST.get('admissionYear', '').strip()
            duration = request.POST.get('duration', '').strip()
            batch_name = request.POST.get('batchName', '').strip()
            status = request.POST.get('status', 'active')
            total_course_fee = request.POST.get('totalCourseFee', '').strip()
            payment_type = request.POST.get('paymentType', 'full')
            number_of_installments = request.POST.get('numberOfInstallments', '').strip()
            
            # Validate required fields
            if not course_id or not department_id or not admission_year:
                return JsonResponse({
                    'success': False,
                    'message': 'Course, department, and admission year are required'
                })
            
            # Validate foreign keys
            try:
                course = Course.objects.get(id=course_id)
                department = Department.objects.get(id=department_id)
            except Course.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid course selected'
                })
            except Department.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid department selected'
                })
            
            # Extract numeric duration from string (e.g., "4 years" -> 4)
            #duration_value = 4   Default duration
            if duration:
                try:
                    # Extract first number from string
                    import re
                    match = re.search(r'\d+', duration)
                    if match:
                        duration_value = int(match.group())
                except ValueError:
                    duration_value = 4  # Fallback to default
            
            # Clean and convert total course fee
            clean_fee = float(total_course_fee.replace(',', '')) if total_course_fee else 0.0
            
            # Validate installment data if payment type is installment
            if payment_type == 'installment' and not number_of_installments:
                return JsonResponse({
                    'success': False,
                    'message': 'Number of installments is required when payment type is installments'
                })
            
            # Generate batch name if not provided
            if not batch_name:
                batch_name = f"{course.course_name} - {department.name} ({admission_year}-{int(admission_year) + duration_value})"
            
            # Check if batch already exists for same department and admission year
            if Batch.objects.filter(
                department=department,
                admission_year=int(admission_year)
            ).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Batch already exists for {department.name} department with admission year {admission_year}'
                })
            
            # Create new batch
            batch = Batch.objects.create(
                name=batch_name,
                course=course,
                department=department,
                admission_year=int(admission_year),
                duration=duration_value,
                total_course_fee=clean_fee,
                payment_type=payment_type,
                number_of_installments=int(number_of_installments) if number_of_installments else None,
                status=status
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Batch "{batch.name}" added successfully',
                'batch': {
                    'id': batch.id,
                    'name': batch.name,
                    'course': batch.course.course_name,
                    'department': batch.department.name,
                    'admission_year': batch.admission_year,
                    'duration': batch.duration,
                    'total_course_fee': str(batch.total_course_fee),
                    'payment_type': batch.get_payment_type_display(),
                    'number_of_installments': batch.number_of_installments,
                    'status': batch.status,
                    'created_at': batch.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error adding batch: {str(e)}'
            })
    
    # If GET request, return error
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


def get_batches(request):
    """API endpoint to get all batches for management table"""
    if request.method == 'GET':
        batches = Batch.objects.all().order_by('-admission_year', 'name')
        
        batches_data = []
        for batch in batches:
            batches_data.append({
                'id': batch.id,
                'name': batch.name,
                'course': batch.course.course_name,
                'department': batch.department.name,
                'admission_year': batch.admission_year,
                'duration': batch.duration,
                'status': batch.status,
                'created_at': batch.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': batch.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'batches': batches_data
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


def get_departments_dropdown(request):
    """API endpoint to get all departments for dropdown"""
    if request.method == 'GET':
        departments = Department.objects.all().order_by('name')
        
        departments_data = []
        for department in departments:
            departments_data.append({
                'id': department.id,
                'name': department.name
            })
        
        return JsonResponse({
            'success': True,
            'departments': departments_data
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_subjects_dropdown(request):
    """API endpoint to get all subjects for dropdown"""
    if request.method == 'GET':
        subjects = Subject.objects.filter(is_active=True).order_by('subject_name')
        
        subjects_data = []
        for subject in subjects:
            subjects_data.append({
                'id': subject.id,
                'name': subject.subject_name,
                'code': subject.subject_code
            })
        
        return JsonResponse({
            'success': True,
            'subjects': subjects_data
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def save_timetable(request):
    """API endpoint to save timetable data to database"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            department_id = data.get('department_id')
            semester = data.get('semester')
            timetable_entries = data.get('timetable_entries', [])
            
            # Validate required fields
            if not department_id or not semester:
                return JsonResponse({
                    'success': False,
                    'message': 'Department and semester are required'
                })
            
            # Clear existing timetable entries for this department and semester
            Timetable.objects.filter(department_id=department_id, semester=semester).delete()
            
            # Save new timetable entries
            print(f"Received {len(timetable_entries)} entries to save:")
            for i, entry in enumerate(timetable_entries):
                print(f"Entry {i+1}: day={entry.get('day')}, time_slot={entry.get('time_slot')}, subject={entry.get('subject')}, room={entry.get('room')}")
            
            for entry in timetable_entries:
                Timetable.objects.create(
                    department_id=department_id,
                    semester=semester,
                    day=entry['day'],
                    time_slot=entry['time_slot'],
                    subject=entry['subject'],
                    room=entry['room']
                )
                print(f"Saved entry: day={entry['day']}, time_slot={entry['time_slot']}, subject={entry['subject']}")
            
            return JsonResponse({
                'success': True,
                'message': f'Timetable saved successfully for semester {semester}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error saving timetable: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_timetables(request):
    """API endpoint to get all saved timetables"""
    if request.method == 'GET':
        try:
            # Get unique timetables grouped by department and semester
            timetables = Timetable.objects.values(
                'department_id', 'department__name', 'semester'
            ).annotate(
                entry_count=Count('id'),
                created_at=Max('created_at')  # Get latest creation time
            ).order_by('-created_at')
            
            timetable_list = []
            for tt in timetables:
                # Get a sample room for this department-semester combination
                sample_entry = Timetable.objects.filter(
                    department_id=tt['department_id'], 
                    semester=tt['semester']
                ).first()
                
                timetable_list.append({
                    'id': f"{tt['department_id']}_sem_{tt['semester']}",
                    'department_id': tt['department_id'],
                    'department_name': tt['department__name'],
                    'semester': tt['semester'],
                    'room': sample_entry.room if sample_entry else 'N/A',
                    'entry_count': tt['entry_count'],
                    'created_date': tt['created_at'].strftime('%Y-%m-%d %H:%M'),
                    'status': 'Active'
                })
            
            return JsonResponse({
                'success': True,
                'timetables': timetable_list
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error fetching timetables: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_timetable_details(request):
    """API endpoint to get detailed timetable for a specific department and semester"""
    if request.method == 'GET':
        try:
            department_id = request.GET.get('department_id')
            semester = request.GET.get('semester')
            
            if not department_id or not semester:
                return JsonResponse({
                    'success': False,
                    'message': 'Department and semester are required'
                })
            
            timetables = Timetable.objects.filter(
                department_id=department_id, 
                semester=semester
            ).order_by('day', 'time_slot')
            
            # Get lunch time from any entry (all entries for this timetable should have same lunch time)
            first_entry = timetables.first()
            lunch_time = None
            if first_entry:
                # Find lunch time by checking which time slot is marked as lunch
                lunch_entries = Timetable.objects.filter(
                    department_id=department_id,
                    semester=semester,
                    subject='LUNCH'
                )
                print(f"Found {lunch_entries.count()} lunch entries for department {department_id}, semester {semester}")
                if lunch_entries.exists():
                    lunch_entry = lunch_entries.first()
                    lunch_time = lunch_entry.time_slot
                    print(f"Found lunch entry: time_slot={lunch_time}")
                else:
                    print("No lunch entries found in database")
            else:
                print("No entries found at all for this timetable")
            
            timetable_entries = []
            for tt in timetables:
                entry_data = {
                    'day': tt.day,
                    'time_slot': tt.time_slot,
                    'subject': tt.subject,
                    'room': tt.room
                }
                timetable_entries.append(entry_data)
                if tt.subject == 'LUNCH':
                    print(f"Lunch entry in results: {entry_data}")
            
            print(f"Total entries: {len(timetable_entries)}, Lunch time: {lunch_time}")
            print(f"All time slots in results: {[entry['time_slot'] for entry in timetable_entries if entry['subject'] == 'LUNCH']}")
            
            return JsonResponse({
                'success': True,
                'timetable_entries': timetable_entries,
                'lunch_time': lunch_time
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error fetching timetable details: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def delete_timetable(request):
    """API endpoint to delete a timetable"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            department_id = data.get('department_id')
            semester = data.get('semester')
            
            if not department_id or not semester:
                return JsonResponse({
                    'success': False,
                    'message': 'Department and semester are required'
                })
            
            # Delete all timetable entries for this department and semester
            deleted_count, _ = Timetable.objects.filter(
                department_id=department_id, 
                semester=semester
            ).delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Timetable deleted successfully. {deleted_count} entries removed.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting timetable: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_batches_dropdown(request):
    """API endpoint to get all batches for dropdown"""
    if request.method == 'GET':
        batches = Batch.objects.filter(status='active').order_by('-admission_year', 'name')
        
        batches_data = []
        for batch in batches:
            end_year = batch.admission_year + batch.duration
            batches_data.append({
                'id': batch.id,
                'name': f"{batch.course.course_name} - {batch.department.name} ({batch.admission_year}–{end_year})"
            })
        
        return JsonResponse({
            'success': True,
            'batches': batches_data
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


def get_batch_current_semester(request):
    """API endpoint to get current semester for a batch"""
    if request.method == 'GET':
        batch_id = request.GET.get('batch_id', '').strip()
        
        if not batch_id:
            return JsonResponse({
                'success': False,
                'message': 'Batch ID is required'
            })
        
        try:
            batch = Batch.objects.get(id=batch_id)
            
            # Calculate current semester based on admission year and duration
            from datetime import datetime
            current_year = datetime.now().year
            
            # Calculate years since admission
            years_since_admission = current_year - batch.admission_year
            
            # Calculate current semester (2 semesters per year)
            current_semester = min(years_since_admission * 2, batch.duration * 2)
            
            # Ensure semester is at least 1
            current_semester = max(1, current_semester)
            
            # Generate roll number format: [AdmissionYearShort]-[DeptCode]/[Serial]
            admission_year_short = str(batch.admission_year)[-2:]  # Last 2 digits
            dept_code = batch.department.code or 'GEN'  # Use department code or default to GEN
            
            # Count existing students in this batch to generate unique serial number
            existing_students_count = Student.objects.filter(
                course=batch.course.course_name,
                batch__contains=str(batch.admission_year)
            ).count()
            serial = str(existing_students_count + 1).zfill(2)  # Generate sequential serial number
            
            # Generate roll number
            roll_number = f"{admission_year_short}-{dept_code}/{serial}"
            
            # Generate email format: [AdmissionYearShort][DeptCode][Serial]@bcet.in
            email = f"{admission_year_short}{dept_code.lower()}{serial}@bcet.in"
            
            return JsonResponse({
                'success': True,
                'current_semester': current_semester,
                'max_semester': batch.duration * 2,
                'roll_number': roll_number,
                'email': email,
                'batch_info': {
                    'name': batch.name,
                    'course': batch.course.course_name,
                    'department': batch.department.name,
                    'department_code': batch.department.code,
                    'admission_year': batch.admission_year,
                    'duration': batch.duration
                }
            })
            
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Batch not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error getting batch semester: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


def delete_batch(request, batch_id):
    """API endpoint to delete a batch"""
    if request.method == 'POST':
        try:
            batch = get_object_or_404(Batch, id=batch_id)
            batch_name = batch.name
            batch.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Batch "{batch_name}" deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting batch: {str(e)}'
            })
    
    # If GET request, return error
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

# Library Management Views
def add_book(request):
    """API endpoint to add a new book"""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('bookTitle', '').strip()
            author = request.POST.get('bookAuthor', '').strip()
            isbn = request.POST.get('bookIsbn', '').strip()
            publisher = request.POST.get('bookPublisher', '').strip()
            publication_year = request.POST.get('publicationYear', '').strip()
            category = request.POST.get('bookCategory', '').strip()
            total_copies = request.POST.get('totalCopies', '1').strip()
            subject_id = request.POST.get('subjectSelect', '').strip()
            description = request.POST.get('bookDescription', '').strip()
            
            # Validate required fields
            if not title or not author or not isbn or not subject_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Title, author, ISBN, and subject are required'
                })
            
            # Validate foreign keys
            try:
                subject = Subject.objects.get(id=subject_id)
            except Subject.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid subject selected'
                })
            
            # Create new book
            book = Book.objects.create(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher,
                publication_year=int(publication_year) if publication_year else datetime.now().year,
                category=category,
                total_copies=int(total_copies),
                available_copies=int(total_copies),
                description=description,
                subject=subject
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Book "{book.title}" added successfully',
                'book': {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn,
                    'subject': book.subject.subject_name,
                    'available_copies': book.available_copies,
                    'total_copies': book.total_copies
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error adding book: {str(e)}'
            })
    
    # If GET request, return error
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_student_books(request):
    """Get books available for student based on their department and semester"""
    if request.method == 'GET':
        try:
            student_email = request.session.get('student_email')
            if not student_email:
                return JsonResponse({
                    'success': False,
                    'message': 'Student not logged in'
                })
            
            student = Student.objects.get(email=student_email, status='approved')
            
            # Get subjects for student's department and semester from timetable
            timetable_entries = Timetable.objects.filter(
                department__name=student.department,
                semester=int(student.semester)
            ).values_list('subject', flat=True).distinct()
            
            # Get books for those subjects
            books = Book.objects.filter(
                subject__subject_name__in=timetable_entries,
                is_active=True,
                available_copies__gt=0
            ).select_related('subject').order_by('title')
            
            books_data = []
            for book in books:
                books_data.append({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn,
                    'subject': book.subject.subject_name,
                    'category': book.category,
                    'available_copies': book.available_copies,
                    'total_copies': book.total_copies,
                    'publication_year': book.publication_year,
                    'cover_image': book.cover_image.url if book.cover_image else None
                })
            
            return JsonResponse({
                'success': True,
                'books': books_data,
                'total': len(books_data)
            })
            
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error fetching books: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def issue_book(request):
    """Issue a book to a student"""
    if request.method == 'POST':
        try:
            student_email = request.session.get('student_email')
            if not student_email:
                return JsonResponse({
                    'success': False,
                    'message': 'Student not logged in'
                })
            
            book_id = request.POST.get('bookId', '').strip()
            if not book_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Book ID is required'
                })
            
            student = Student.objects.get(email=student_email, status='approved')
            book = Book.objects.get(id=book_id)
            
            # Check if book is available
            if book.available_copies <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Book is not available'
                })
            
            # Check if student already has this book issued
            existing_issue = BookIssue.objects.filter(
                student=student,
                book=book,
                status='issued'
            ).first()
            
            if existing_issue:
                return JsonResponse({
                    'success': False,
                    'message': 'You already have this book issued'
                })
            
            # Check student's current issued books count (max 3)
            current_issues = BookIssue.objects.filter(
                student=student,
                status='issued'
            ).count()
            
            if current_issues >= 3:
                return JsonResponse({
                    'success': False,
                    'message': 'You cannot issue more than 3 books at a time'
                })
            
            # Calculate due date (14 days from now)
            from datetime import date, timedelta
            due_date = date.today() + timedelta(days=14)
            
            # Create book issue
            book_issue = BookIssue.objects.create(
                book=book,
                student=student,
                due_date=due_date
            )
            
            # Update available copies
            book.available_copies -= 1
            book.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Book "{book.title}" issued successfully',
                'due_date': due_date.strftime('%Y-%m-%d'),
                'issue_date': book_issue.issue_date.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except (Student.DoesNotExist, Book.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Student or book not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error issuing book: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_student_book_issues(request):
    """Get student's current and past book issues"""
    if request.method == 'GET':
        try:
            student_email = request.session.get('student_email')
            if not student_email:
                return JsonResponse({
                    'success': False,
                    'message': 'Student not logged in'
                })
            
            student = Student.objects.get(email=student_email, status='approved')
            
            # Get student's book issues
            book_issues = BookIssue.objects.filter(
                student=student
            ).select_related('book').order_by('-issue_date')
            
            issues_data = []
            for issue in book_issues:
                issues_data.append({
                    'id': issue.id,
                    'book_title': issue.book.title,
                    'book_author': issue.book.author,
                    'book_isbn': issue.book.isbn,
                    'issue_date': issue.issue_date.strftime('%Y-%m-%d'),
                    'due_date': issue.due_date.strftime('%Y-%m-%d'),
                    'return_date': issue.return_date.strftime('%Y-%m-%d %H:%M:%S') if issue.return_date else None,
                    'status': issue.status,
                    'fine_amount': float(issue.fine_amount),
                    'is_overdue': issue.is_overdue()
                })
            
            return JsonResponse({
                'success': True,
                'issues': issues_data,
                'total': len(issues_data)
            })
            
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error fetching book issues: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def return_book(request):
    """Return a book"""
    if request.method == 'POST':
        try:
            student_email = request.session.get('student_email')
            if not student_email:
                return JsonResponse({
                    'success': False,
                    'message': 'Student not logged in'
                })
            
            issue_id = request.POST.get('issueId', '').strip()
            if not issue_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Issue ID is required'
                })
            
            student = Student.objects.get(email=student_email, status='approved')
            book_issue = BookIssue.objects.get(id=issue_id, student=student)
            
            if book_issue.status != 'issued':
                return JsonResponse({
                    'success': False,
                    'message': 'Book is already returned'
                })
            
            # Calculate fine if overdue
            from datetime import date
            fine_amount = 0.00
            if book_issue.is_overdue():
                days_overdue = (date.today() - book_issue.due_date).days
                fine_amount = min(days_overdue * 2.00, 50.00)  # Rs. 2 per day, max Rs. 50
            
            # Update book issue
            book_issue.status = 'returned'
            book_issue.return_date = datetime.now()
            book_issue.fine_amount = fine_amount
            book_issue.save()
            
            # Update book available copies
            book_issue.book.available_copies += 1
            book_issue.book.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Book returned successfully',
                'fine_amount': float(fine_amount)
            })
            
        except (Student.DoesNotExist, BookIssue.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Student or issue not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error returning book: {str(e)}'
            })


# Admin Account Management Views
def create_admin(request):
    """Create new admin account (only accessible by primary admin)"""
    admin_username = request.session.get('admin_username')
    if not admin_username:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    try:
        current_admin = Admin.objects.get(username=admin_username, status='active')
        if not current_admin.is_primary_admin():
            return JsonResponse({'success': False, 'message': 'Access denied. Only primary admin can create admin accounts.'})
    except Admin.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        status = request.POST.get('status', 'active')
        
        # Validation
        if not all([full_name, email]):
            return JsonResponse({'success': False, 'message': 'Full name and email are required'})
        
        if Admin.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists'})
        
        # Auto-generate username from email (part before @)
        import re
        username = email.split('@')[0]
        username = re.sub(r'[^a-zA-Z0-9]', '', username)  # Remove special characters
        
        # Ensure username is unique
        original_username = username
        counter = 1
        while Admin.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        # Auto-generate password internally
        import random
        import string
        password = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=12))
        
        # Create new admin with default role 'admin' (no full_name field in Admin model)
        admin = Admin.objects.create(
            username=username,
            email=email,
            password=password,  # In production, use proper hashing
            role='admin',  # Default role for all new admins
            status=status
        )
        
        # Send email with credentials
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = 'Your Admin Account Credentials - Student 360 Platform'
            message = f'''
Dear {full_name},

Your admin account has been successfully created for the Student 360 Platform.

Login Credentials:
- Username: {username}
- Password: {password}
- Login URL: {request.build_absolute_uri('/login/')}

Please keep these credentials secure and change your password after first login.

Role: Academic Admin
Status: {status.title()}

If you have any questions, please contact the system administrator.

Best regards,
Student 360 Platform Team
            '''
            
            send_mail(
                subject,
                message,
                'annonmusk00@gmail.com',
                [email],
                fail_silently=False,
            )
            
            email_sent = True
            email_message = "Login credentials have been sent to the email address."
            
        except Exception as e:
            email_sent = False
            email_message = f"Admin account created but email failed to send. Error: {str(e)}"
        
        return JsonResponse({
            'success': True,
            'message': f'Admin account created successfully! {email_message}',
            'email_sent': email_sent,
            'admin': {
                'username': admin.username,
                'email': admin.email,
                'role': admin.role,
                'status': admin.status,
                'created_at': admin.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def deactivate_admin(request, admin_id):
    """Deactivate admin account (only accessible by primary admin)"""
    admin_username = request.session.get('admin_username')
    if not admin_username:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    try:
        current_admin = Admin.objects.get(username=admin_username, status='active')
        if not current_admin.is_primary_admin():
            return JsonResponse({'success': False, 'message': 'Access denied. Only primary admin can deactivate admin accounts.'})
    except Admin.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    try:
        admin_to_deactivate = Admin.objects.get(id=admin_id)
        
        # Prevent deactivating primary admin
        if admin_to_deactivate.is_primary_admin():
            return JsonResponse({'success': False, 'message': 'Cannot deactivate primary admin account'})
        
        # Prevent self-deactivation
        if admin_to_deactivate.username == current_admin.username:
            return JsonResponse({'success': False, 'message': 'Cannot deactivate your own account'})
        
        admin_to_deactivate.status = 'inactive'
        admin_to_deactivate.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Admin account deactivated successfully'
        })
        
    except Admin.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Admin account not found'})


def delete_admin(request, admin_id):
    """Delete admin account (only accessible by primary admin)"""
    admin_username = request.session.get('admin_username')
    if not admin_username:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    try:
        current_admin = Admin.objects.get(username=admin_username, status='active')
        if not current_admin.is_primary_admin():
            return JsonResponse({'success': False, 'message': 'Access denied. Only primary admin can delete admin accounts.'})
    except Admin.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    if request.method == 'POST':
        try:
            admin_to_delete = Admin.objects.get(id=admin_id)
            
            # Prevent deleting primary admin
            if admin_to_delete.is_primary_admin():
                return JsonResponse({'success': False, 'message': 'Cannot delete primary admin account'})
            
            # Prevent self-deletion
            if admin_to_delete.username == current_admin.username:
                return JsonResponse({'success': False, 'message': 'Cannot delete your own account'})
            
            # Store username for message
            deleted_username = admin_to_delete.username
            
            # Delete the admin account
            admin_to_delete.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Admin account "{deleted_username}" has been permanently deleted'
            })
            
        except Admin.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Admin account not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def reset_admin_password(request, admin_id):
    """Reset admin password (only accessible by primary admin)"""
    admin_username = request.session.get('admin_username')
    if not admin_username:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    try:
        current_admin = Admin.objects.get(username=admin_username, status='active')
        if not current_admin.is_primary_admin():
            return JsonResponse({'success': False, 'message': 'Access denied. Only primary admin can reset admin passwords.'})
    except Admin.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        
        if not new_password or len(new_password) < 6:
            return JsonResponse({'success': False, 'message': 'Password must be at least 6 characters long'})
        
        try:
            admin_to_reset = Admin.objects.get(id=admin_id)
            admin_to_reset.password = new_password  # In production, use proper hashing
            admin_to_reset.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Password reset successfully'
            })
            
        except Admin.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Admin account not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def change_admin_password(request):
    """Change current admin's own password"""
    admin_username = request.session.get('admin_username')
    if not admin_username:
        return JsonResponse({'success': False, 'message': 'Admin not logged in'})
    
    if request.method == 'POST':
        try:
            current_admin = Admin.objects.get(username=admin_username, status='active')
            
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Check if current password is hashed or plain text
            if current_admin.password.startswith('pbkdf2_sha256$'):
                # Password is already hashed, use check_password
                if not check_password(current_password, current_admin.password):
                    return JsonResponse({'success': False, 'message': 'Current password is incorrect'})
            else:
                # Password is still plain text, check directly
                if current_admin.password != current_password:
                    return JsonResponse({'success': False, 'message': 'Current password is incorrect'})
            
            # Validate new password
            if not new_password or len(new_password) < 6:
                return JsonResponse({'success': False, 'message': 'New password must be at least 6 characters long'})
            
            # Check if passwords match
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': 'New passwords do not match'})
            
            # Update password with proper hashing
            current_admin.password = make_password(new_password)
            current_admin.save()
            
            return JsonResponse({'success': True, 'message': 'Password changed successfully'})
            
        except Admin.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Admin account not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def forgot_password(request):
    """Handle forgot password requests"""
    if request.method == 'POST':
        email = request.POST.get('email')
        user_role = request.POST.get('userRole')
        
        try:
            if user_role == 'admin':
                # Check if admin exists with matching email
                admin = Admin.objects.get(email=email, status='active')
                
                # Delete any existing tokens for this admin
                PasswordResetToken.objects.filter(user_type='admin', user_id=admin.id).delete()
                
                # Create new token
                token = PasswordResetToken.objects.create(
                    user_type='admin',
                    user_id=admin.id,
                    email=email,
                    expires_at=timezone.now() + timezone.timedelta(hours=1)  # Token expires in 1 hour
                )
                
                # Send email with reset link
                reset_link = request.build_absolute_uri(f'/reset-password/{token.token}/')
                subject = "Password Reset Request - Student 360 Platform"
                message = f"""
Hello {admin.username},

You requested a password reset for your admin account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
Student 360 Platform Team
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'nore@student360.com',
                        [email],
                        fail_silently=False,
                    )
                    return JsonResponse({'success': True, 'message': f'Password reset link has been sent to {email}. Please check your email.'})
                except Exception as e:
                    return JsonResponse({'success': False, 'message': f'Failed to send email: {str(e)}'})
                
            elif user_role == 'teacher':
                # Check if teacher exists with matching email
                teacher = Teacher.objects.get(email=email)
                
                # Delete any existing tokens for this teacher
                PasswordResetToken.objects.filter(user_type='teacher', user_id=teacher.id).delete()
                
                # Create new token
                token = PasswordResetToken.objects.create(
                    user_type='teacher',
                    user_id=teacher.id,
                    email=email,
                    expires_at=timezone.now() + timezone.timedelta(hours=1)  # Token expires in 1 hour
                )
                
                # Send email with reset link
                reset_link = request.build_absolute_uri(f'/reset-password/{token.token}/')
                subject = "Password Reset Request - Student 360 Platform"
                message = f"""
Hello {teacher.first_name} {teacher.last_name},

You requested a password reset for your teacher account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
Student 360 Platform Team
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'nore@student360.com',
                        [email],
                        fail_silently=False,
                    )
                    return JsonResponse({'success': True, 'message': f'Password reset link has been sent to {email}. Please check your email.'})
                except Exception as e:
                    return JsonResponse({'success': False, 'message': f'Failed to send email: {str(e)}'})
                
            else:
                return JsonResponse({'success': False, 'message': 'Invalid role selected'})
                
        except Admin.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No admin account found with this email'})
        except Teacher.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No teacher account found with this email'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def reset_password(request, token):
    """Handle password reset with token"""
    if request.method == 'GET':
        try:
            reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
            
            # Check if token is expired
            if reset_token.is_expired():
                return render(request, 'reset_password.html', {
                    'error': 'This reset link has expired. Please request a new password reset.',
                    'token_valid': False
                })
            
            return render(request, 'reset_password.html', {
                'token': token,
                'token_valid': True,
                'user_type': reset_token.user_type,
                'email': reset_token.email
            })
            
        except PasswordResetToken.DoesNotExist:
            return render(request, 'reset_password.html', {
                'error': 'Invalid reset link. Please request a new password reset.',
                'token_valid': False
            })
    
    elif request.method == 'POST':
        try:
            reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
            
            # Check if token is expired
            if reset_token.is_expired():
                return JsonResponse({'success': False, 'message': 'This reset link has expired.'})
            
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate passwords
            if not new_password or len(new_password) < 6:
                return JsonResponse({'success': False, 'message': 'Password must be at least 6 characters long.'})
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': 'Passwords do not match.'})
            
            # Update user password
            if reset_token.user_type == 'admin':
                admin = Admin.objects.get(id=reset_token.user_id)
                admin.password = make_password(new_password)
                admin.save()
            elif reset_token.user_type == 'teacher':
                try:
                    teacher = Teacher.objects.get(id=reset_token.user_id)
                    teacher.password = make_password(new_password)  # Hash and update password
                    teacher.teacher_code = new_password  # Also update teacher_code as backup
                    teacher.save()
                except Teacher.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Teacher account not found.'})
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            return JsonResponse({'success': True, 'message': 'Password reset successfully! You can now login with your new password.'})
            
        except PasswordResetToken.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid reset link.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def transfer_primary_role(request, admin_id):
    """Transfer primary admin role (only accessible by current primary admin)"""
    admin_username = request.session.get('admin_username')
    if not admin_username:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    try:
        current_admin = Admin.objects.get(username=admin_username, status='active')
        if not current_admin.is_primary_admin():
            return JsonResponse({'success': False, 'message': 'Access denied. Only primary admin can transfer primary role.'})
    except Admin.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Not authenticated'})
    
    if request.method == 'POST':
        try:
            new_primary_admin = Admin.objects.get(id=admin_id, status='active')
            
            # Demote current primary admin to regular admin
            current_admin.role = 'admin'
            current_admin.save()
            
            # Promote selected admin to primary
            new_primary_admin.role = 'primary'
            new_primary_admin.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Primary admin role transferred successfully'
            })
            
        except Admin.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Admin account not found or not active'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def scrape_bput_sessions(request):
    """
    Scrape session options from BPUT results website
    """
    if request.method == 'GET':
        try:
            # Headers from the curl request - REMOVE Accept-Encoding to handle compression manually
            headers = {
                'Sec-Ch-Ua': '"Chromium";v="119", "Not?A_Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                # Remove Accept-Encoding to let requests handle it automatically
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'close'
            }
            
            # Try multiple URLs that might have the form
            urls_to_try = [
                'https://results.bput.ac.in',
                'https://results.bput.ac.in/',
                'https://results.bput.ac.in/index.php',
                'https://results.bput.ac.in/result.php',
                'https://bput.ac.in/results',
                'http://results.bput.ac.in'
            ]
            
            response = None
            for url in urls_to_try:
                try:
                    print(f"Trying URL: {url}")
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    print(f"Success with URL: {url}")
                    break
                except requests.exceptions.RequestException as e:
                    print(f"Failed with URL {url}: {e}")
                    continue
            
            if not response:
                raise requests.exceptions.RequestException("All URLs failed")
            
            # Debug: Print response info
            print(f"Response status: {response.status_code}")
            print(f"Response content type: {response.headers.get('content-type', 'Unknown')}")
            print(f"Response content length: {len(response.content)}")
            print(f"Encoding: {response.encoding}")
            
            # Check if response is actually HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                print(f"Warning: Response is not HTML (content-type: {content_type})")
                print(f"First 200 chars: {response.text[:200]}")
                # Fall back to default sessions
                raise requests.exceptions.RequestException("Non-HTML response received")
            
            # Parse the HTML content - use response.text which handles encoding automatically
            try:
                html_content = response.text
                print(f"Successfully decoded HTML content, length: {len(html_content)}")
                print(f"First 100 chars: {html_content[:100]}")
                soup = BeautifulSoup(html_content, 'html.parser')
            except Exception as e:
                print(f"Error parsing HTML: {e}")
                print(f"Response content preview: {response.text[:500]}")
                raise requests.exceptions.RequestException(f"HTML parsing failed: {e}")
            
            # Debug: Check if we got HTML content
            if not soup.find('html'):
                print("Warning: No HTML tag found in response")
                print(f"Response text preview: {response.text[:500]}")
                # Try to parse anyway - maybe it's a fragment
                print("Attempting to parse as HTML fragment...")
            
            # Find all select elements and extract option values
            session_options = []
            select_elements = soup.find_all('select')
            
            # Debug: Print what we found
            print(f"Found {len(select_elements)} select elements")
            for i, select in enumerate(select_elements):
                print(f"Select {i}: name='{select.get('name', 'no-name')}', id='{select.get('id', 'no-id')}'")
                options = select.find_all('option')
                print(f"  Options: {len(options)}")
                for j, option in enumerate(options[:3]):  # Show first 3 options
                    print(f"    Option {j}: value='{option.get('value', '')}', text='{option.get_text(strip=True)[:50]}'")
            
            for select in select_elements:
                # Get the select name/id if available
                select_name = select.get('name', select.get('id', 'unknown'))
                
                # Extract options from this select
                options = []
                for option in select.find_all('option'):
                    option_value = option.get('value', '')
                    option_text = option.get_text(strip=True)
                    if option_text:  # Only include non-empty options
                        options.append({
                            'value': option_value,
                            'text': option_text
                        })
                
                if options:  # Only include selects that have options
                    session_options.append({
                        'select_name': select_name,
                        'options': options
                    })
            
            return JsonResponse({
                'success': True,
                'data': session_options,
                'message': f'Successfully scraped {len(session_options)} select elements with options'
            })
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            # Return fallback session options
            fallback_sessions = [
                {
                    'select_name': 'session',
                    'options': [
                        {'value': 'Odd-(2025-26)', 'text': 'Odd-(2025-26)'},
                        {'value': 'Even-(2025-26)', 'text': 'Even-(2025-26)'},
                        {'value': 'Odd-(2024-25)', 'text': 'Odd-(2024-25)'},
                        {'value': 'Even-(2024-25)', 'text': 'Even-(2024-25)'},
                        {'value': 'Odd-(2023-24)', 'text': 'Odd-(2023-24)'},
                        {'value': 'Even-(2023-24)', 'text': 'Even-(2023-24)'}
                    ]
                }
            ]
            return JsonResponse({
                'success': True,
                'data': fallback_sessions,
                'message': 'Using fallback session options due to scraping failure'
            })
        except Exception as e:
            print(f"Error scraping data: {e}")
            # Return fallback session options
            fallback_sessions = [
                {
                    'select_name': 'session',
                    'options': [
                        {'value': 'Odd-(2025-26)', 'text': 'Odd-(2025-26)'},
                        {'value': 'Even-(2025-26)', 'text': 'Even-(2025-26)'},
                        {'value': 'Odd-(2024-25)', 'text': 'Odd-(2024-25)'},
                        {'value': 'Even-(2024-25)', 'text': 'Even-(2024-25)'},
                        {'value': 'Odd-(2023-24)', 'text': 'Odd-(2023-24)'},
                        {'value': 'Even-(2023-24)', 'text': 'Even-(2023-24)'}
                    ]
                }
            ]
            return JsonResponse({
                'success': True,
                'data': fallback_sessions,
                'message': 'Using fallback session options due to error'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method. Use GET.'
    })


def get_bput_result(request):
    """
    Fetch actual result from BPUT website using POST request
    """
    if request.method == 'POST':
        try:
            # Get form data
            session = request.POST.get('session', '')
            reg_no = request.POST.get('regNo', '')
            dob = request.POST.get('dob', '')
            
            if not session or not reg_no or not dob:
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields: session, regNo, dob'
                })
            
            # Headers for the POST request - REMOVE Accept-Encoding to handle compression manually
            headers = {
                'Content-Length': '0',
                'Sec-Ch-Ua': '"Chromium";v="119", "Not?A_Brand";v="24"',
                'Accept': '*/*',
                'Content-Type': 'application/json; charset=utf-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Sec-Ch-Ua-Mobile': '?0',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Origin': 'https://results.bput.ac.in',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://results.bput.ac.in/',
                # Remove Accept-Encoding to let requests handle it automatically
                'Accept-Language': 'en-US,en;q=0.9',
                'Priority': 'u=1, i'
            }
            
            # Extract semester ID from session (this might need adjustment based on actual BPUT logic)
            # For now, we'll try to map session to semester ID
            session_to_semester = {
                'Odd-(2025-26)': '7',
                'Even-(2025-26)': '8',
                'Odd-(2024-25)': '5',
                'Even-(2024-25)': '6',
                'Odd-(2023-24)': '3',
                'Even-(2023-24)': '4'
            }
            
            semester_id = session_to_semester.get(session, '7')  # Default to 7
            
            # Make the POST request to BPUT
            post_url = f'https://results.bput.ac.in/student-results-subjects-list?semid={semester_id}&rollNo={reg_no}&session={session}'
            
            print(f"Making POST request to: {post_url}")
            print(f"Semester ID: {semester_id}, Roll No: {reg_no}, Session: {session}")
            
            response = requests.post(post_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            print(f"Response status: {response.status_code}")
            print(f"Response content type: {response.headers.get('content-type', 'Unknown')}")
            print(f"Response length: {len(response.content)}")
            print(f"Response encoding: {response.encoding}")
            
            # Parse the response - use response.text which handles encoding automatically
            try:
                # Use response.text to handle compression automatically
                json_text = response.text
                print(f"JSON text preview: {json_text[:200]}")
                
                result_data = response.json()
                print(f"Successfully parsed JSON response: {result_data}")
                
                return JsonResponse({
                    'success': True,
                    'data': result_data,
                    'message': 'Result fetched successfully from BPUT'
                })
                
            except ValueError as e:
                # If not JSON, try to parse as HTML
                print(f"JSON parsing failed: {e}")
                print("Response is not JSON, trying to parse as HTML...")
                html_content = response.text
                print(f"HTML content preview: {html_content[:500]}")
                
                # Here you would parse the HTML to extract result information
                # For now, return the HTML content for debugging
                return JsonResponse({
                    'success': True,
                    'html_content': html_content,
                    'message': 'Result HTML fetched (needs parsing)'
                })
            except Exception as e:
                print(f"Error parsing response: {e}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error parsing result: {str(e)}'
                })
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Failed to fetch result: {str(e)}'
            })
        except Exception as e:
            print(f"Error processing result: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error processing result: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method. Use POST.'
    })

# Quiz View Functions
def create_quiz(request):
    """Create a new quiz for teacher"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    teacher_email = request.session.get('teacher_email')
    if not teacher_email:
        return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
    
    try:
        teacher = Teacher.objects.get(email=teacher_email)
        
        # Get form data
        title = request.POST.get('title')
        subject_id = request.POST.get('subject')
        duration = request.POST.get('duration')
        total_questions = request.POST.get('total_questions')
        total_marks = request.POST.get('total_marks')
        instructions = request.POST.get('instructions')
        start_datetime = request.POST.get('start_datetime')
        end_datetime = request.POST.get('end_datetime')
        
        # Debug: Print received data
        print(f"DEBUG: Received quiz creation data:")
        print(f"  title: {title}")
        print(f"  subject_id: {subject_id}")
        print(f"  duration: {duration}")
        print(f"  total_questions: {total_questions}")
        print(f"  total_marks: {total_marks}")
        print(f"  instructions: {instructions}")
        print(f"  start_datetime: {start_datetime}")
        print(f"  end_datetime: {end_datetime}")
        print(f"  POST data keys: {list(request.POST.keys())}")
        
        # Validate required fields
        if not all([title, subject_id, duration, total_questions, total_marks]):
            missing_fields = []
            if not title: missing_fields.append('title')
            if not subject_id: missing_fields.append('subject')
            if not duration: missing_fields.append('duration')
            if not total_questions: missing_fields.append('total_questions')
            if not total_marks: missing_fields.append('total_marks')
            return JsonResponse({'success': False, 'message': f'All required fields must be filled. Missing: {", ".join(missing_fields)}'})
        
        # Get subject
        subject = Subject.objects.get(id=subject_id)
        
        # Parse datetime fields
        from datetime import datetime
        start_date = None
        end_date = None
        
        if start_datetime:
            try:
                start_date = datetime.fromisoformat(start_datetime)
                print(f"DEBUG: Raw start_datetime from browser: {start_datetime}")
                print(f"DEBUG: Parsed naive start_date: {start_date}")
                if timezone.is_naive(start_date):
                    # Treat naive datetime as local time (browser datetime-local)
                    # Use current timezone from Django settings
                    start_date = timezone.make_aware(start_date)
                    print(f"DEBUG: Localized start_date: {start_date}")
                else:
                    print(f"DEBUG: Start_date already timezone-aware: {start_date}")
            except ValueError:
                start_date = timezone.now()
                print(f"DEBUG: Using timezone.now() as fallback: {start_date}")
        else:
            start_date = timezone.now()
            print(f"DEBUG: No start_datetime provided, using timezone.now(): {start_date}")
            
        if end_datetime:
            try:
                end_date = datetime.fromisoformat(end_datetime)
                if timezone.is_naive(end_date):
                    # Treat naive datetime as local time (browser datetime-local)
                    # Use current timezone from Django settings
                    end_date = timezone.make_aware(end_date)
            except ValueError:
                end_date = timezone.now() + timezone.timedelta(days=7)
        else:
            end_date = timezone.now() + timezone.timedelta(days=7)
        
        # Create quiz
        quiz = Quiz.objects.create(
            title=title,
            subject=subject,
            teacher=teacher,
            department=subject.department,
            semester=subject.semester,
            duration_minutes=int(duration),
            total_questions=int(total_questions),
            total_marks=float(total_marks),
            instructions=instructions,
            start_date=start_date,
            end_date=end_date
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Quiz created successfully',
            'quiz_id': quiz.id
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Subject not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error creating quiz: {str(e)}'})

def get_teacher_quizzes(request):
    """Get all quizzes created by the teacher"""
    teacher_email = request.session.get('teacher_email')
    if not teacher_email:
        return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
    
    try:
        teacher = Teacher.objects.get(email=teacher_email)
        quizzes = Quiz.objects.filter(teacher=teacher).select_related('subject', 'department').order_by('-created_date')
        
        quiz_data = []
        for quiz in quizzes:
            # Determine quiz status
            status = 'draft'
            if not quiz.is_published:
                status = 'draft'
            elif quiz.is_active_now():
                status = 'active'
            elif quiz.is_upcoming():
                status = 'published'
            elif quiz.is_active:
                status = 'published'
            else:
                status = 'expired'
                
            quiz_data.append({
                'id': quiz.id,
                'title': quiz.title,
                'subject': quiz.subject.subject_name,
                'department': quiz.department.name,
                'semester': quiz.semester,
                'duration_minutes': quiz.duration_minutes,
                'total_questions': quiz.total_questions,
                'total_marks': quiz.total_marks,
                'is_active': quiz.is_active,
                'is_published': quiz.is_published,
                'status': status,
                'start_date': timezone.localtime(quiz.start_date).strftime('%Y-%m-%d %H:%M'),
                'end_date': timezone.localtime(quiz.end_date).strftime('%Y-%m-%d %H:%M'),
                'created_date': quiz.created_date.strftime('%Y-%m-%d %H:%M'),
                'is_active_now': quiz.is_active_now(),
                'is_upcoming': quiz.is_upcoming(),
            })
        
        return JsonResponse({
            'success': True,
            'quizzes': quiz_data
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error fetching quizzes: {str(e)}'})

def create_quiz_question(request):
    """Create a new question for a quiz"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    teacher_email = request.session.get('teacher_email')
    if not teacher_email:
        return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
    
    try:
        teacher = Teacher.objects.get(email=teacher_email)
        
        # Get form data
        quiz_id = request.POST.get('quiz_id')
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type')
        marks = request.POST.get('marks')
        explanation = request.POST.get('explanation', '')
        
        # Validate required fields
        if not all([quiz_id, question_text, question_type, marks]):
            return JsonResponse({'success': False, 'message': 'All required fields must be filled'})
        
        # Get quiz
        quiz = Quiz.objects.get(id=quiz_id, teacher=teacher)
        
        # Normalize question type to database format
        normalized_type = question_type
        if question_type == 'multiple-choice':
            normalized_type = 'mcq'
        elif question_type == 'true-false':
            normalized_type = 'true_false'
        
        # Create question
        question = QuizQuestion.objects.create(
            quiz=quiz,
            question_text=question_text,
            question_type=normalized_type,
            marks=float(marks),
            order=quiz.questions.count() + 1
        )
        
        # Create options based on question type
        if normalized_type == 'mcq':
            options = request.POST.getlist('options')
            correct_option = request.POST.get('correct_option')
            
            # Debug: Print options data
            print(f"DEBUG: Creating MCQ options")
            print(f"DEBUG: Raw options from POST: {options}")
            print(f"DEBUG: Correct option index: {correct_option}")
            print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
            
            for i, option_text in enumerate(options):
                print(f"DEBUG: Processing option {i}: '{option_text}'")
                if option_text.strip():
                    option = QuizOption.objects.create(
                        question=question,
                        option_text=option_text,
                        is_correct=(str(i) == correct_option),
                        order=i + 1
                    )
                    print(f"DEBUG: Created option: {option.option_text} (Correct: {option.is_correct})")
                else:
                    print(f"DEBUG: Skipping empty option {i}")
        
        # Handle true/false questions
        elif normalized_type == 'true_false':
            correct_answer = request.POST.get('correct_answer')
            if correct_answer:
                # Create True option
                QuizOption.objects.create(
                    question=question,
                    option_text='True',
                    is_correct=(correct_answer.lower() == 'true'),
                    order=1
                )
                # Create False option
                QuizOption.objects.create(
                    question=question,
                    option_text='False',
                    is_correct=(correct_answer.lower() == 'false'),
                    order=2
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Question created successfully',
            'question_id': question.id
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except Quiz.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quiz not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error creating question: {str(e)}'})

def get_quiz_questions(request, quiz_id):
    """Get all questions for a quiz"""
    teacher_email = request.session.get('teacher_email')
    if not teacher_email:
        return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
    
    try:
        teacher = Teacher.objects.get(email=teacher_email)
        quiz = Quiz.objects.get(id=quiz_id, teacher=teacher)
        
        questions = QuizQuestion.objects.filter(quiz=quiz).prefetch_related('options').order_by('order')
        
        questions_data = []
        for question in questions:
            question_data = {
                'id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'marks': question.marks,
                'order': question.order,
                'options': []
            }
            
            if question.question_type in ['mcq', 'true_false']:
                for option in question.options.all():
                    question_data['options'].append({
                        'id': option.id,
                        'option_text': option.option_text,
                        'is_correct': option.is_correct,
                        'order': option.order
                    })
            
            questions_data.append(question_data)
        
        return JsonResponse({
            'success': True,
            'questions': questions_data
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except Quiz.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quiz not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error fetching questions: {str(e)}'})

def publish_quiz(request, quiz_id):
    """Publish a quiz to make it available to students"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    teacher_email = request.session.get('teacher_email')
    if not teacher_email:
        return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
    
    try:
        teacher = Teacher.objects.get(email=teacher_email)
        quiz = Quiz.objects.get(id=quiz_id, teacher=teacher)
        
        # Check if quiz has questions
        question_count = QuizQuestion.objects.filter(quiz=quiz).count()
        if question_count == 0:
            return JsonResponse({'success': False, 'message': 'Please add questions before publishing the quiz'})
        
        # Update quiz to publish it
        quiz.is_published = True
        quiz.is_active = True
        quiz.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Quiz published successfully! Students can now take this quiz.'
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except Quiz.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quiz not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error publishing quiz: {str(e)}'})

def delete_quiz(request, quiz_id):
    """Delete a quiz and all its questions"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    teacher_email = request.session.get('teacher_email')
    if not teacher_email:
        return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
    
    try:
        teacher = Teacher.objects.get(email=teacher_email)
        quiz = Quiz.objects.get(id=quiz_id, teacher=teacher)
        
        # Delete the quiz (questions and options will be deleted due to CASCADE)
        quiz.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Quiz deleted successfully'
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except Quiz.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quiz not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error deleting quiz: {str(e)}'})

def delete_quiz_question(request, question_id):
    """Delete a quiz question"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    teacher_email = request.session.get('teacher_email')
    if not teacher_email:
        return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
    
    try:
        teacher = Teacher.objects.get(email=teacher_email)
        question = QuizQuestion.objects.get(id=question_id, quiz__teacher=teacher)
        
        # Delete the question (options will be deleted due to CASCADE)
        question.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Question deleted successfully'
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except QuizQuestion.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Question not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error deleting question: {str(e)}'})

def start_quiz(request, quiz_id):
    """Start a quiz for a student"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    student_email = request.session.get('student_email')
    if not student_email:
        return JsonResponse({'success': False, 'message': 'Student not logged in'})
    
    try:
        student = Student.objects.get(college_email=student_email, status='approved')
        quiz = Quiz.objects.get(id=quiz_id, is_active=True)
        
        # Check if student has already attempted this quiz
        existing_attempt = QuizAttempt.objects.filter(quiz=quiz, student=student).first()
        if existing_attempt:
            if existing_attempt.status == 'completed':
                return JsonResponse({'success': False, 'message': 'You have already completed this quiz'})
            elif existing_attempt.status == 'in_progress':
                return JsonResponse({'success': True, 'attempt_id': existing_attempt.id, 'message': 'Resuming existing attempt'})
        
        # Check if quiz is currently active
        if not quiz.is_active_now():
            if quiz.is_upcoming():
                return JsonResponse({'success': False, 'message': 'Quiz has not started yet'})
            else:
                return JsonResponse({'success': False, 'message': 'Quiz has ended'})
        
        # Create new quiz attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=student,
            start_time=timezone.now(),
            status='in_progress'
        )
        
        return JsonResponse({
            'success': True,
            'attempt_id': attempt.id,
            'message': 'Quiz started successfully'
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student not found'})
    except Quiz.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quiz not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error starting quiz: {str(e)}'})

def take_quiz(request, attempt_id):
    """Display quiz questions for student to take"""
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('login')
    
    try:
        student = Student.objects.get(college_email=student_email, status='approved')
        attempt = QuizAttempt.objects.get(id=attempt_id, student=student)
        
        # Check if attempt can be continued
        if attempt.status not in ['in_progress', 'not_started']:
            return render(request, 'quiz_error.html', {
                'error': 'This quiz cannot be taken at this time',
                'student': student
            })
        
        # Check if quiz is still active and within time limits
        if not attempt.quiz.is_active_now():
            return render(request, 'quiz_error.html', {
                'error': 'This quiz is not currently active',
                'student': student
            })
        
        # Get quiz questions with options
        questions = QuizQuestion.objects.filter(quiz=attempt.quiz).prefetch_related('options')
        
        # Debug: Print question information
        print(f"DEBUG: Quiz ID: {attempt.quiz.id}")
        print(f"DEBUG: Quiz Title: {attempt.quiz.title}")
        print(f"DEBUG: Found {questions.count()} questions for this quiz")
        for question in questions:
            print(f"DEBUG: Question: {question.question_text} (Type: {question.question_type})")
            print(f"DEBUG: Options count: {question.options.count()}")
            for option in question.options.all():
                print(f"DEBUG: Option: {option.option_text} (Correct: {option.is_correct})")
        
        # If questions should be shuffled, shuffle them
        if attempt.quiz.shuffle_questions:
            questions = list(questions)
            import random
            random.shuffle(questions)
        
        context = {
            'student': student,
            'attempt': attempt,
            'quiz': attempt.quiz,
            'questions': questions,
            'time_left': calculate_time_left(attempt)
        }
        
        return render(request, 'take_quiz.html', context)
        
    except (Student.DoesNotExist, QuizAttempt.DoesNotExist):
        return redirect('student_status')

def quiz_results(request, attempt_id):
    """Display quiz results for a completed attempt"""
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('login')
    
    try:
        student = Student.objects.get(college_email=student_email, status='approved')
        attempt = QuizAttempt.objects.get(id=attempt_id, student=student)
        
        if attempt.status != 'completed':
            return redirect('take_quiz', attempt_id=attempt_id)
        
        # Get answers with questions and correct options
        answers = QuizAnswer.objects.filter(attempt=attempt).select_related('question', 'selected_option')
        
        context = {
            'student': student,
            'attempt': attempt,
            'quiz': attempt.quiz,
            'answers': answers,
            'total_questions': attempt.quiz.total_questions,
            'correct_answers': answers.filter(is_correct=True).count(),
            'time_taken': attempt.total_time_taken
        }
        
        # Store results in session for display on dashboard
        request.session['quiz_results'] = {
            'success': True,
            'message': 'Quiz completed successfully',
            'results': {
                'marks_obtained': float(attempt.marks_obtained),
                'percentage': float(attempt.percentage),
                'correct_answers': answers.filter(is_correct=True).count(),
                'total_questions': attempt.quiz.total_questions,
                'quiz_title': attempt.quiz.title
            }
        }
        
        return redirect('student_status')
        
    except (Student.DoesNotExist, QuizAttempt.DoesNotExist):
        return redirect('student_status')

def submit_quiz(request, attempt_id):
    """Submit quiz answers"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    student_email = request.session.get('student_email')
    if not student_email:
        return JsonResponse({'success': False, 'message': 'Student not logged in'})
    
    try:
        student = Student.objects.get(college_email=student_email, status='approved')
        attempt = QuizAttempt.objects.get(id=attempt_id, student=student, status='in_progress')
        
        # Parse answers from form data
        answers_data = {}
        print(f"DEBUG: Quiz submission POST data: {dict(request.POST)}")
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.replace('question_', '')
                answers_data[question_id] = value
                print(f"DEBUG: Found answer for question {question_id}: {value}")
        
        print(f"DEBUG: Total answers parsed: {len(answers_data)}")
        
        total_marks = 0
        correct_answers = 0
        
        # Process each answer
        for question_id, answer_value in answers_data.items():
            try:
                question = QuizQuestion.objects.get(id=question_id, quiz=attempt.quiz)
                
                # Create or update answer
                answer, created = QuizAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'text_answer': answer_value if question.question_type != 'mcq' else '',
                    }
                )
                
                # Check if answer is correct and calculate marks
                if question.question_type == 'mcq' and answer_value:
                    selected_option = QuizOption.objects.get(id=answer_value)
                    answer.selected_option = selected_option
                    answer.is_correct = selected_option.is_correct
                    answer.marks_obtained = question.marks if selected_option.is_correct else 0
                elif question.question_type == 'true_false':
                    answer.is_correct = (answer_value.lower() == 'true')
                    answer.marks_obtained = question.marks if answer.is_correct else 0
                elif question.question_type == 'short_answer':
                    # For short answers, you might implement text matching logic
                    answer.is_correct = False  # Placeholder
                    answer.marks_obtained = 0  # Placeholder
                
                if answer.is_correct:
                    total_marks += question.marks
                    correct_answers += 1
                
                answer.save()
                
            except (QuizQuestion.DoesNotExist, QuizOption.DoesNotExist):
                continue
        
        # Update attempt with results
        attempt.marks_obtained = total_marks
        attempt.percentage = (total_marks / attempt.quiz.total_marks) * 100 if attempt.quiz.total_marks > 0 else 0
        attempt.end_time = timezone.now()
        attempt.status = 'completed'
        
        # Calculate time taken
        if attempt.start_time:
            time_diff = attempt.end_time - attempt.start_time
            attempt.total_time_taken = int(time_diff.total_seconds())
        
        attempt.save()
        
        # Store results in session for display on dashboard
        request.session['quiz_results'] = {
            'success': True,
            'message': 'Quiz submitted successfully',
            'results': {
                'marks_obtained': float(total_marks),
                'percentage': float(attempt.percentage),
                'correct_answers': correct_answers,
                'total_questions': attempt.quiz.total_questions,
                'quiz_title': attempt.quiz.title
            }
        }
        
        return redirect('student_status')
        
    except (Student.DoesNotExist, QuizAttempt.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'Invalid attempt'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error submitting quiz: {str(e)}'})

def calculate_time_left(attempt):
    """Calculate time left for quiz attempt"""
    if attempt.status != 'in_progress' or not attempt.start_time:
        return 0
    
    now = timezone.now()
    end_time = attempt.start_time + timezone.timedelta(minutes=attempt.quiz.duration_minutes)
    time_left = end_time - now
    
    return max(0, int(time_left.total_seconds()))


def get_quiz_responses(request, quiz_id):
    """Get all responses for a quiz"""
    try:
        # Check if teacher is logged in
        teacher_email = request.session.get('teacher_email')
        if not teacher_email:
            return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
        
        teacher = Teacher.objects.get(email=teacher_email)
        quiz = Quiz.objects.get(id=quiz_id, teacher=teacher)
        
        # Get all attempts for this quiz
        attempts = QuizAttempt.objects.filter(quiz=quiz).select_related('student')
        
        responses = []
        for attempt in attempts:
            response_data = {
                'attempt_id': attempt.id,
                'student_name': f"{attempt.student.first_name} {attempt.student.last_name}",
                'student_id': attempt.student.student_id,
                'submitted_at': attempt.end_time.isoformat() if attempt.end_time else attempt.created_at.isoformat(),
                'status': attempt.status,
                'marks_obtained': float(attempt.marks_obtained) if attempt.marks_obtained else 0,
                'total_marks': float(quiz.total_marks),
                'percentage': float(attempt.percentage) if attempt.percentage else 0,
                'time_taken': f"{attempt.total_time_taken // 60} min {attempt.total_time_taken % 60} sec" if attempt.total_time_taken else None,
            }
            responses.append(response_data)
        
        # Calculate statistics
        total_attempts = attempts.count()
        completed_attempts = attempts.filter(status='completed')
        
        average_score = 0
        pass_rate = 0
        
        if completed_attempts.exists():
            total_score = sum(attempt.percentage for attempt in completed_attempts if attempt.percentage)
            average_score = total_score / completed_attempts.count()
            
            passing_attempts = completed_attempts.filter(percentage__gte=quiz.passing_marks / quiz.total_marks * 100)
            pass_rate = (passing_attempts.count() / completed_attempts.count()) * 100
        
        statistics = {
            'total_attempts': total_attempts,
            'average_score': round(average_score, 1),
            'pass_rate': round(pass_rate, 1)
        }
        
        return JsonResponse({
            'success': True,
            'responses': responses,
            'statistics': statistics
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except Quiz.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quiz not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def get_response_details(request, attempt_id):
    """Get detailed response for a specific attempt"""
    try:
        # Check if teacher is logged in
        teacher_email = request.session.get('teacher_email')
        if not teacher_email:
            return JsonResponse({'success': False, 'message': 'Teacher not logged in'})
        
        teacher = Teacher.objects.get(email=teacher_email)
        attempt = QuizAttempt.objects.get(id=attempt_id)
        
        # Verify that this attempt belongs to a quiz created by this teacher
        if attempt.quiz.teacher != teacher:
            return JsonResponse({'success': False, 'message': 'Unauthorized access'})
        
        # Get all answers for this attempt
        answers = QuizAnswer.objects.filter(attempt=attempt).select_related('question', 'selected_option')
        
        answer_details = []
        for answer in answers:
            answer_data = {
                'question_text': answer.question.question_text,
                'question_type': answer.question.question_type,
                'marks': float(answer.question.marks),
                'marks_obtained': float(answer.marks_obtained) if answer.marks_obtained else 0,
                'is_correct': answer.is_correct,
                'text_answer': answer.text_answer,
                'selected_answer': answer.selected_option.option_text if answer.selected_option else None,
                'correct_answer': None,
            }
            
            # Add correct answer for MCQ questions
            if answer.question.question_type == 'mcq':
                correct_option = QuizOption.objects.filter(question=answer.question, is_correct=True).first()
                if correct_option:
                    answer_data['correct_answer'] = correct_option.option_text
            elif answer.question.question_type == 'true_false':
                correct_option = QuizOption.objects.filter(question=answer.question, is_correct=True).first()
                if correct_option:
                    answer_data['correct_answer'] = correct_option.option_text
            
            answer_details.append(answer_data)
        
        response_data = {
            'attempt_id': attempt.id,
            'student_name': f"{attempt.student.first_name} {attempt.student.last_name}",
            'student_id': attempt.student.student_id,
            'submitted_at': attempt.end_time.isoformat() if attempt.end_time else attempt.created_at.isoformat(),
            'status': attempt.status,
            'marks_obtained': float(attempt.marks_obtained) if attempt.marks_obtained else 0,
            'total_marks': float(attempt.quiz.total_marks),
            'percentage': float(attempt.percentage) if attempt.percentage else 0,
            'time_taken': f"{attempt.total_time_taken // 60} min {attempt.total_time_taken % 60} sec" if attempt.total_time_taken else None,
            'answers': answer_details
        }
        
        return JsonResponse({
            'success': True,
            'response': response_data
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Teacher not found'})
    except QuizAttempt.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Attempt not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
