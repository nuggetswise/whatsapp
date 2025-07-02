"""
PDF Text Extraction Utility
Minimal utility for extracting text from PDF files.
All hardcoded resume review logic has been moved to the newsletter-grounded system.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_text_from_pdf(pdf_file) -> Optional[str]:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_file: File path (string) or file-like object
    
    Returns:
        Extracted text as string, or None if extraction fails
    """
    try:
        import PyPDF2
        import io
        
        if hasattr(pdf_file, 'read'):
            # File-like object - read content and create BytesIO
            content = pdf_file.read()
            # Reset file pointer to beginning in case it's needed elsewhere
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        else:
            # File path
            pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# Legacy compatibility notice
def process_resume_review(*args, **kwargs):
    """
    Legacy function - now handled by NewsletterGroundedReviewer.
    Please use the new newsletter-grounded system instead.
    """
    raise DeprecationWarning(
        "process_resume_review has been replaced by NewsletterGroundedReviewer. "
        "Please use core.whatsapp_prompt.NewsletterGroundedReviewer instead."
    ) 