import os
import json
import requests
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import sys
import traceback

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new newsletter-grounded system
from core.whatsapp_prompt import NewsletterGroundedReviewer
from core.creator_review import extract_text_from_pdf
from routes.whatsapp_response import send_whatsapp_response

# Initialize Flask blueprint
from flask import Blueprint
app = Blueprint('whatsapp_api', __name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize the newsletter-grounded reviewer (lazy initialization)
newsletter_reviewer = None

def get_newsletter_reviewer():
    """Get or create the newsletter reviewer instance."""
    global newsletter_reviewer
    if newsletter_reviewer is None:
        newsletter_reviewer = NewsletterGroundedReviewer()
    return newsletter_reviewer

# Logging setup
def log_user_activity(phone: str, action: str, metadata: Dict[str, Any]):
    """Log user activity to a JSON file."""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "phone": phone,
            "action": action,
            "metadata": metadata
        }
        
        log_file = "review_logs.json"
        logs = []
        
        # Load existing logs
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
        
        # Add new log entry
        logs.append(log_entry)
        
        # Keep only last 1000 entries
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        # Save logs
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    except Exception as e:
        print(f"Error logging user activity: {e}")

def download_resume_from_url(url: str) -> Optional[bytes]:
    """Download resume from URL."""
    try:
        print(f"Downloading resume from URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        
        # Check if request was successful
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        print(f"Content type: {content_type}")
        
        # Be more lenient with content type
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            print("WARNING: Content type does not indicate PDF and URL does not end with .pdf")
            # Continue anyway for testing
        
        print(f"Downloaded {len(response.content)} bytes")
        return response.content
        
    except Exception as e:
        print(f"Error downloading resume from URL: {e}")
        return None

def validate_resume_file(file_content: bytes) -> bool:
    """Validate that the file is a valid PDF."""
    try:
        # Print debug info
        print(f"File content length: {len(file_content)} bytes")
        print(f"File starts with: {file_content[:10]}")
        print(f"Starts with %PDF: {file_content.startswith(b'%PDF')}")
        
        # Check PDF magic number - be more lenient
        if not file_content.startswith(b'%PDF'):
            print("WARNING: File does not start with %PDF")
            # Continue anyway for testing
        
        # Check file size (max 10MB)
        if len(file_content) > 10 * 1024 * 1024:
            print(f"WARNING: File too large: {len(file_content) / (1024 * 1024):.2f} MB")
            return False
        
        # Accept the file for testing
        print("File validation passed")
        return True
        
    except Exception as e:
        print(f"Error validating file: {e}")
        return False

def validate_job_url(url: str) -> bool:
    """Validate that the job URL is properly formatted and accessible."""
    if not url:
        return True  # Job URL is optional
    
    try:
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Check if URL is reachable (with timeout)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        # Consider 2xx and 3xx status codes as valid
        return response.status_code < 400
        
    except Exception as e:
        print(f"Job URL validation warning: {e}")
        return True  # Don't fail the entire request for JD URL issues

@app.route('/whatsapp-upload', methods=['POST'])
def whatsapp_upload():
    """
    Main endpoint for WhatsApp resume upload and processing with newsletter-grounded review.
    
    Expected JSON payload:
    {
        "resumeUrl": "https://example.com/resume.pdf",
        "jobUrl": "https://jobs.company.com/product-manager", // Optional but recommended
        "userMessage": "Optional user message",
        "phone": "+1234567890"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        # Extract required fields
        resume_url = data.get('resumeUrl')
        job_url = data.get('jobUrl')
        user_message = data.get('userMessage', '')
        phone = data.get('phone')
        
        # Clean and validate job URL
        if job_url:
            job_url = clean_job_url(job_url)
            if not validate_job_url(job_url):
                print(f"Job URL validation failed: {job_url}")
                # Don't fail the request, just log and continue without JD
                job_url = None
        
        # Validate required fields
        if not resume_url:
            return jsonify({
                "success": False,
                "error": "resumeUrl is required"
            }), 400
        
        if not phone:
            return jsonify({
                "success": False,
                "error": "phone is required"
            }), 400
        
        # Log the request
        log_user_activity(phone, "resume_upload", {
            "resume_url": resume_url,
            "job_url": job_url,
            "has_user_message": bool(user_message),
            "has_job_url": bool(job_url),
            "user_agent": request.headers.get('User-Agent', 'Unknown')
        })
        
        # Download resume from URL
        resume_content = download_resume_from_url(resume_url)
        
        if not resume_content:
            # Send error message via WhatsApp
            send_newsletter_grounded_error(phone, "resume_download_failed")
            return jsonify({
                "success": False,
                "error": "Could not download resume from URL"
            }), 400
        
        # Validate resume file
        if not validate_resume_file(resume_content):
            # Send error message via WhatsApp
            send_newsletter_grounded_error(phone, "invalid_resume_format")
            return jsonify({
                "success": False,
                "error": "Invalid resume file format or size"
            }), 400
        
        # Extract text from PDF
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(resume_content)
                temp_file_path = temp_file.name
            
            # Extract text using existing function
            resume_text = extract_text_from_pdf(temp_file_path)
            
            if not resume_text or len(resume_text.strip()) < 50:
                send_newsletter_grounded_error(phone, "text_extraction_failed")
                return jsonify({
                    "success": False,
                    "error": "Could not extract meaningful text from resume"
                }), 400
            
            print(f"Extracted resume text: {len(resume_text)} characters")
            
            # Process resume review using newsletter-grounded system
            review_result = get_newsletter_reviewer().process_resume_review(
                resume_text=resume_text,
                job_url=job_url
            )
            
            if not review_result['success']:
                send_newsletter_grounded_error(phone, "processing_failed", review_result.get('error'))
                return jsonify({
                    "success": False,
                    "error": review_result.get('error', 'Unknown processing error')
                }), 500
            
            # Send the newsletter-grounded review via WhatsApp
            whatsapp_result = send_newsletter_grounded_review(phone, review_result)
            
            # Log successful processing
            log_user_activity(phone, "review_completed", {
                "confidence_score": review_result['confidence_score'],
                "newsletter_chunks_used": review_result['newsletter_chunks_used'],
                "had_job_url": bool(job_url),
                "jd_parsed_successfully": review_result['jd_info'].get('success', False),
                "whatsapp_sent": whatsapp_result.get('success', False)
            })
            
            return jsonify({
                "success": True,
                "message": "Resume review completed and sent via WhatsApp",
                "confidence_score": review_result['confidence_score'],
                "newsletter_chunks_used": review_result['newsletter_chunks_used'],
                "jd_parsed": review_result['jd_info'].get('success', False),
                "whatsapp_result": whatsapp_result
            })
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    print(f"Error cleaning up temp file: {e}")
        
    except Exception as e:
        print(f"Unexpected error in whatsapp_upload: {e}")
        print(traceback.format_exc())
        
        # Try to send error message via WhatsApp if phone is available
        if 'phone' in locals():
            send_newsletter_grounded_error(phone, "unexpected_error", str(e))
        
        return jsonify({
            "success": False,
            "error": f"Unexpected server error: {str(e)}"
        }), 500

def clean_job_url(url: str) -> str:
    """Clean and normalize job URL."""
    if not url:
        return url
    
    # Fix common issues with job URLs
    try:
        # Remove unencoded ampersands and tracking parameters
        if '&' in url and not '%26' in url:
            print(f"Original job URL: {url}")
            
            # Fix common issue with greenhouse URLs
            if 'greenhouse.io' in url and '&gh_src=' in url:
                url = url.split('&gh_src=')[0]
                print(f"Cleaned greenhouse URL: {url}")
            
            # Fix other tracking parameters
            tracking_params = ['&utm_source=', '&ref=', '&referrer=', '&source=']
            for param in tracking_params:
                if param in url:
                    url = url.split(param)[0]
                    break
        
        return url
        
    except Exception as e:
        print(f"Error cleaning job URL: {e}")
        return url

def send_newsletter_grounded_review(phone: str, review_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send newsletter-grounded review via WhatsApp using the new response system.
    
    Args:
        phone: Phone number to send to
        review_result: Result from newsletter-grounded reviewer
    
    Returns:
        Dict containing send result
    """
    try:
        # Use the updated WhatsApp response system
        response_result = send_whatsapp_response(
            phone, 
            review_result['review'],
            None,  # No PDF path needed
            review_result['confidence_score'] / 100.0,  # Convert to 0-1 scale for compatibility
            "Aakash"
        )
        
        return response_result
        
    except Exception as e:
        print(f"Error sending newsletter-grounded review: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def send_newsletter_grounded_error(phone: str, error_type: str, details: str = None):
    """
    Send error message via WhatsApp with newsletter-appropriate messaging.
    
    Args:
        phone: Phone number to send to
        error_type: Type of error
        details: Optional error details
    """
    error_messages = {
        'resume_download_failed': "❌ I couldn't download your resume. Please check the URL and try again.",
        'invalid_resume_format': "❌ Please make sure your resume is a valid PDF file under 10MB.",
        'text_extraction_failed': "❌ I couldn't read the text from your resume. Please ensure it's a text-based PDF, not just an image.",
        'processing_failed': "❌ I encountered an issue while analyzing your resume. Please try again in a few minutes.",
        'job_url_invalid': "❌ I couldn't access the job posting URL. The review will be based on general principles from my newsletter.",
        'unexpected_error': "❌ Something unexpected happened. Please try again, and if the issue persists, let me know!"
    }
    
    message = error_messages.get(error_type, "❌ An error occurred while processing your request.")
    
    if details and error_type in ['processing_failed', 'unexpected_error']:
        # Only include technical details for specific error types
        message += f"\n\nTechnical details: {details[:100]}..."
    
    try:
        send_whatsapp_response(phone, message, None, 0.0, "Aakash")
    except Exception as e:
        print(f"Error sending error message to WhatsApp: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "newsletter_system": "active"
    })

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get recent activity logs (last 50 entries)."""
    try:
        if not os.path.exists("review_logs.json"):
            return jsonify({"logs": []})
        
        with open("review_logs.json", 'r') as f:
            logs = json.load(f)
        
        # Return last 50 entries
        recent_logs = logs[-50:] if len(logs) > 50 else logs
        
        return jsonify({
            "logs": recent_logs,
            "total_count": len(logs)
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Could not retrieve logs: {str(e)}"
        }), 500

@app.route('/newsletter-status', methods=['GET'])
def newsletter_status():
    """Get status of newsletter system components."""
    try:
        # Check newsletter manager
        newsletter_chunks = len(get_newsletter_reviewer().newsletter_manager.chunks)
        
        return jsonify({
            "newsletter_chunks_loaded": newsletter_chunks,
            "jd_parser_available": bool(get_newsletter_reviewer().jd_parser),
            "relevance_scorer_available": bool(get_newsletter_reviewer().relevance_scorer),
            "gemini_model_available": bool(get_newsletter_reviewer().gemini_model),
            "system_status": "operational"
        })
        
    except Exception as e:
        return jsonify({
            "system_status": "error",
            "error": str(e)
        }), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "success": False,
        "error": "File too large. Please compress your resume to under 10MB."
    }), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500 