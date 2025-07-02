import os
import re
from flask import Blueprint, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

# Import new newsletter-grounded system instead of legacy
from core.whatsapp_prompt import NewsletterGroundedReviewer
from core.creator_review import extract_text_from_pdf
from routes.whatsapp_response import send_whatsapp_response

load_dotenv()

inbound = Blueprint('whatsapp_inbound', __name__)

# Initialize the newsletter-grounded reviewer
reviewer = NewsletterGroundedReviewer()

# Simple regex for URLs
URL_REGEX = r'(https?://\S+)'  # Matches any URL

@inbound.route('/whatsapp-inbound', methods=['POST'])
def whatsapp_inbound():
    """
    Conversational WhatsApp bot endpoint for Twilio webhook.
    Uses the new newsletter-grounded review system.
    """
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    resp = MessagingResponse()

    # Try to extract URLs
    urls = re.findall(URL_REGEX, incoming_msg)
    resume_url, job_url = None, None

    # Heuristic: first URL is resume, second is job (if present)
    if urls:
        resume_url = urls[0]
        if len(urls) > 1:
            job_url = urls[1]

    if resume_url:
        # Trigger the newsletter-grounded review flow
        resp.message("✅ Got your resume! Processing with my newsletter expertise. You'll receive your review soon.")
        
        try:
            # Download and process resume
            import requests
            import io
            
            print(f"Processing resume from URL: {resume_url}")
            resume_content = requests.get(resume_url).content
            resume_text = extract_text_from_pdf(io.BytesIO(resume_content))
            
            if not resume_text or len(resume_text.strip()) < 50:
                resp.message("❌ I couldn't extract meaningful text from your resume. Please ensure it's a text-based PDF.")
                return Response(str(resp), mimetype="application/xml")
            
            # Use the new newsletter-grounded review system
            review_result = reviewer.process_resume_review(resume_text, job_url)
            
            if review_result["success"]:
                # Send the newsletter-grounded review via WhatsApp
                print(f"Sending newsletter-grounded review to {from_number}")
                send_whatsapp_response(
                    from_number.replace('whatsapp:', ''),
                    review_result["review"],
                    None,  # No PDF generation in new system
                    review_result["confidence_score"] / 100.0,  # Convert to 0-1 scale
                    "Aakash"
                )
                
                # Log successful processing
                print(f"Successfully processed resume for {from_number}: confidence={review_result['confidence_score']}, chunks={review_result['newsletter_chunks_used']}")
                
            else:
                # Send error message
                error_msg = "❌ I encountered an issue while analyzing your resume. Please try again, or check that your resume is a valid PDF file."
                send_whatsapp_response(
                    from_number.replace('whatsapp:', ''),
                    error_msg,
                    None, 0.0, "Aakash"
                )
                print(f"Review failed for {from_number}: {review_result.get('error')}")
                
        except Exception as e:
            error_msg = f"❌ Error processing your resume: {str(e)[:100]}..."
            resp.message(error_msg)
            print(f"Exception in whatsapp_inbound for {from_number}: {e}")
            
        return Response(str(resp), mimetype="application/xml")

    # If no resume URL, send help message
    help_msg = (
        "👋 Hi! I'm Aakash's resume review bot powered by my newsletter expertise.\n\n"
        "Send me your resume PDF link (and optionally a job posting URL) and I'll provide personalized feedback grounded in my proven resume optimization principles.\n\n"
        "Example:\nhttps://example.com/resume.pdf https://jobs.company.com/role\n\n"
        "You'll get back expert feedback based on my newsletter content! 📚"
    )
    resp.message(help_msg)
    return Response(str(resp), mimetype="application/xml") 