from django.shortcuts import render
from django.http import JsonResponse
from .models import Book, Subject, Department
from django.db.models import Count
import os
import json
from django.conf import settings
from django.core.files.storage import default_storage
from datetime import datetime

# Simple PDF metadata storage (you could create a proper model later)
PDF_METADATA_FILE = os.path.join(settings.MEDIA_ROOT, 'pdf_metadata.json')

def load_pdf_metadata():
    """Load PDF metadata from JSON file"""
    if os.path.exists(PDF_METADATA_FILE):
        with open(PDF_METADATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_pdf_metadata(metadata):
    """Save PDF metadata to JSON file"""
    with open(PDF_METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def get_books_count(request):
    """Get total books count for admin dashboard"""
    if request.method == 'GET':
        try:
            books_count = Book.objects.count()
            return JsonResponse({
                'success': True,
                'books_count': books_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error getting books count: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def delete_pdf(request):
    """Delete PDF file"""
    if request.method == 'POST':
        try:
            file_name = request.POST.get('fileName', '').strip()
            
            if not file_name:
                return JsonResponse({
                    'success': False,
                    'message': 'File name is required'
                })
            
            # Validate file name to prevent directory traversal
            if '..' in file_name or file_name.startswith('/') or '\\' in file_name:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid file name'
                })
            
            # Construct file path
            file_path = os.path.join(settings.MEDIA_ROOT, 'library_pdfs', file_name)
            
            # Check if file exists
            if os.path.exists(file_path):
                os.remove(file_path)
                
                # Remove from metadata
                metadata = load_pdf_metadata()
                metadata = [item for item in metadata if item['file_name'] != file_name]
                save_pdf_metadata(metadata)
                
                return JsonResponse({
                    'success': True,
                    'message': f'PDF "{file_name}" deleted successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'PDF "{file_name}" not found'
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting PDF: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_books_for_library(request):
    """Get all books for library management"""
    if request.method == 'GET':
        try:
            books = Book.objects.all().select_related('subject').order_by('title')
            
            books_data = []
            for book in books:
                books_data.append({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn,
                    'subject': book.subject.subject_name,
                    'category': book.category,
                    'total_copies': book.total_copies,
                    'available_copies': book.available_copies,
                    'publication_year': book.publication_year,
                    'cover_image': book.cover_image.url if book.cover_image else None,
                    'is_active': book.is_active,
                    'created_at': book.created_at.strftime('%Y-%m-%d')
                })
            
            return JsonResponse({
                'success': True,
                'books': books_data,
                'total': len(books_data)
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

def upload_pdf(request):
    """Upload PDF for student downloads"""
    if request.method == 'POST':
        try:
            # Get form data
            pdf_file = request.FILES.get('pdfFile')
            title = request.POST.get('pdfTitle', '').strip()
            description = request.POST.get('pdfDescription', '').strip()
            branch_id = request.POST.get('pdfBranch', '').strip()
            semester = request.POST.get('pdfSemester', '').strip()
            
            # Validate required fields
            if not pdf_file or not title or not branch_id or not semester:
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required: PDF file, title, branch, and semester'
                })
            
            # Validate file type
            if not pdf_file.name.lower().endswith('.pdf'):
                return JsonResponse({
                    'success': False,
                    'message': 'Only PDF files are allowed'
                })
            
            # Get branch name
            try:
                branch = Department.objects.get(id=branch_id)
                branch_name = branch.name
            except:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid branch selected'
                })
            
            # Create filename with metadata
            filename = f"{branch_name}_{semester}_{pdf_file.name}"
            
            # Save PDF file
            file_path = default_storage.save(f'library_pdfs/{filename}', pdf_file)
            
            # Save metadata
            metadata = load_pdf_metadata()
            metadata.append({
                'title': title,
                'file_name': filename,
                'description': description,
                'branch': branch_name,
                'semester': semester,
                'upload_date': datetime.now().strftime('%Y-%m-%d'),
                'file_size': f'{(pdf_file.size / 1024):.1f} KB',
                'file_path': f'/media/library_pdfs/{filename}'
            })
            save_pdf_metadata(metadata)
            
            return JsonResponse({
                'success': True,
                'message': f'PDF "{title}" uploaded successfully',
                'file_path': f'/media/{file_path}',
                'branch': branch_name,
                'semester': semester
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error uploading PDF: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_pdfs(request):
    """Get all PDFs for student downloads"""
    if request.method == 'GET':
        try:
            # Load PDFs from metadata
            pdfs = load_pdf_metadata()
            
            # Sort by upload date (newest first)
            pdfs.sort(key=lambda x: x['upload_date'], reverse=True)
            
            return JsonResponse({
                'success': True,
                'pdfs': pdfs,
                'total': len(pdfs)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error fetching PDFs: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })
