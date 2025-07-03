import os
import re
import json
from flask import Blueprint, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

# Import new newsletter-grounded system instead of legacy
from core.whatsapp_prompt import NewsletterGroundedReviewer
from core.creator_review import extract_text_from_pdf
from routes.whatsapp_response import send_whatsapp_response
from core.whatsapp_conversation_engine import start_conversation, continue_conversation

load_dotenv()

inbound = Blueprint('whatsapp_inbound', __name__)

# Initialize the newsletter-grounded reviewer
reviewer = NewsletterGroundedReviewer()

# Enhanced regex for URLs that handles spaces and special characters
URL_REGEX = r'(https?://[^\s]+)'  # Matches URLs until whitespace

# In-memory conversation state (in production, use Redis or database)
conversation_state = {}

def get_conversation_state(phone_number):
    """Get conversation state for a phone number."""
    return conversation_state.get(phone_number, {
        'stage': 'initial',
        'resume_url': None,
        'job_url': None,
        'last_review': None,
        'follow_up_questions': [],
        'engine_state': None
    })

def set_conversation_state(phone_number, state):
    """Set conversation state for a phone number."""
    conversation_state[phone_number] = state

def generate_follow_up_questions(review_result):
    """Generate follow-up questions based on the review."""
    questions = [
        "🤔 Would you like me to elaborate on any specific point from the review?",
        "🎯 Should I help you customize your resume for a different role?",
        "📊 Would you like me to analyze a specific section of your resume in more detail?",
        "💡 Should I provide specific examples of how to implement the suggestions?",
        "📝 Would you like me to help you rewrite any bullet points?"
    ]
    return questions[:3]  # Return first 3 questions

def format_quick_replies_text(quick_replies):
    if not quick_replies:
        return ""
    lines = ["\nReply with one of the following options:"]
    for reply in quick_replies:
        lines.append(f"{reply['id']}. {reply['title']}")
    return "\n".join(lines)

@inbound.route('/whatsapp-inbound', methods=['POST'])
def whatsapp_inbound():
    """
    Conversational WhatsApp bot endpoint for Twilio webhook.
    Uses the new newsletter-grounded review system with two-way conversation.
    """
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '').replace('whatsapp:', '')
    resp = MessagingResponse()

    print(f"[DEBUG] Incoming WhatsApp message from {from_number}: '{incoming_msg}'")
    state = get_conversation_state(from_number)
    print(f"[DEBUG] State BEFORE processing for {from_number}: {json.dumps(state, indent=2)}")

    # --- NEW: Handle PDF attachment ---
    num_media = int(request.values.get('NumMedia', 0))
    if num_media > 0:
        media_url = request.values.get('MediaUrl0')
        media_type = request.values.get('MediaContentType0')
        print(f"[DEBUG] Media received: {media_url} ({media_type})")
        if media_type == "application/pdf":
            # Download the PDF and process as resume
            import requests
            import io
            resp.message("✅ Got your PDF resume! Processing with my newsletter expertise. You'll receive your review soon.")
            try:
                resume_response = requests.get(media_url)
                if resume_response.status_code != 200:
                    raise Exception(f"Failed to download PDF: {resume_response.status_code}")
                resume_content = resume_response.content
                resume_text = extract_text_from_pdf(io.BytesIO(resume_content))
                if not resume_text or len(resume_text.strip()) < 100:
                    resp.message("❌ I couldn't extract meaningful text from your resume. Please ensure it's a text-based PDF.")
                    state['stage'] = 'initial'
                    set_conversation_state(from_number, state)
                    return Response(str(resp), mimetype="application/xml")
                # Use the new engine to start the conversation
                review_result = reviewer.process_resume_review(resume_text, None)
                if review_result["success"]:
                    resume_data = review_result
                    job_data = {"title": review_result.get("job_title", "this role"), "company": review_result.get("company", "the company")}
                    messages, engine_state = start_conversation("User", resume_data, job_data)
                    state['engine_state'] = engine_state
                    state['stage'] = 'conversation'
                    set_conversation_state(from_number, state)
                    for msg in messages:
                        content = msg['content']
                        resp.message(content)
                else:
                    resp.message("❌ I encountered an issue while analyzing your resume. Please try again, or check that your resume is a valid PDF file.")
                    state['stage'] = 'initial'
                    set_conversation_state(from_number, state)
            except Exception as e:
                resp.message(f"❌ Error processing your resume: {str(e)[:100]}...")
                state['stage'] = 'initial'
                set_conversation_state(from_number, state)
            print(f"[DEBUG] State AFTER processing for {from_number}: {json.dumps(state, indent=2)}")
            return Response(str(resp), mimetype="application/xml")
        else:
            resp.message("❌ Please send your resume as a PDF file.")
            return Response(str(resp), mimetype="application/xml")
    # --- END NEW ---

    # If no state or initial, expect resume URL
    if not state.get('engine_state') or state.get('stage') == 'initial':
        urls = re.findall(URL_REGEX, incoming_msg)
        resume_url, job_url = None, None
        if urls:
            resume_url = urls[0]
            if len(urls) > 1:
                job_url = urls[1]
        if resume_url:
            # Detect document type (simple heuristic)
            if resume_url.lower().endswith('.pdf') or 'resume' in resume_url.lower():
                state['doc_type'] = 'resume'
            elif 'job' in resume_url.lower() or 'jd' in resume_url.lower():
                state['doc_type'] = 'job_description'
            else:
                state['doc_type'] = 'other'
            state['resume_url'] = resume_url
            state['job_url'] = job_url
            state['stage'] = 'processing'
            set_conversation_state(from_number, state)
            print(f"[DEBUG] State AFTER processing for {from_number}: {json.dumps(state, indent=2)}")
            resp.message("✅ Got your resume! Processing with my newsletter expertise. You'll receive your review soon.")
            try:
                import requests
                import io
                resume_response = requests.get(resume_url)
                if resume_response.status_code != 200:
                    raise Exception(f"Failed to download PDF: {resume_response.status_code}")
                resume_content = resume_response.content
                resume_text = extract_text_from_pdf(io.BytesIO(resume_content))
                if not resume_text or len(resume_text.strip()) < 100:
                    resp.message("❌ I couldn't extract meaningful text from your resume. Please ensure it's a text-based PDF.")
                    state['stage'] = 'initial'
                    set_conversation_state(from_number, state)
                    return Response(str(resp), mimetype="application/xml")
                # Use the new engine to start the conversation
                # Simulate resume_data and job_data from review_result for now
                review_result = reviewer.process_resume_review(resume_text, job_url)
                if review_result["success"]:
                    resume_data = review_result
                    job_data = {"title": review_result.get("job_title", "this role"), "company": review_result.get("company", "the company")}
                    messages, engine_state = start_conversation("User", resume_data, job_data)
                    # Store engine state
                    state['engine_state'] = engine_state
                    state['stage'] = 'conversation'
                    set_conversation_state(from_number, state)
                    # Send all messages
                    for msg in messages:
                        content = msg['content']
                        # Always append next step prompt and quick replies
                        if 'quick_replies' in msg and msg['quick_replies']:
                            content += "\n\nWhat would you like to do next?" + format_quick_replies_text(msg['quick_replies'])
                        resp.message(content)
                else:
                    resp.message("❌ I encountered an issue while analyzing your resume. Please try again, or check that your resume is a valid PDF file.")
                    state['stage'] = 'initial'
                    set_conversation_state(from_number, state)
            except Exception as e:
                resp.message(f"❌ Error processing your resume: {str(e)[:100]}...")
                state['stage'] = 'initial'
                set_conversation_state(from_number, state)
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
    # If in conversation, use the engine for follow-ups
    elif state.get('engine_state'):
        engine_state = state['engine_state']
        messages, new_engine_state = continue_conversation(incoming_msg, engine_state)
        state['engine_state'] = new_engine_state
        set_conversation_state(from_number, state)
        print(f"[DEBUG] State AFTER processing for {from_number}: {json.dumps(state, indent=2)}")
        for msg in messages:
            content = msg['content']
            # Always append next step prompt and quick replies
            if 'quick_replies' in msg and msg['quick_replies']:
                content += "\n\nWhat would you like to do next?" + format_quick_replies_text(msg['quick_replies'])
            resp.message(content)
        return Response(str(resp), mimetype="application/xml")
    # Fallback
    else:
        state['stage'] = 'initial'
        set_conversation_state(from_number, state)
        print(f"[DEBUG] State AFTER processing for {from_number}: {json.dumps(state, indent=2)}")
        resp.message("👋 Hi! I'm Aakash's resume review bot. Send me your resume PDF link to get started!")
        return Response(str(resp), mimetype="application/xml")

@inbound.route('/whatsapp-status', methods=['POST'])
def whatsapp_status():
    """Handle WhatsApp message status callbacks from Twilio."""
    message_sid = request.values.get('MessageSid')
    message_status = request.values.get('MessageStatus')
    to_number = request.values.get('To')
    from_number = request.values.get('From')
    
    print(f"📱 WhatsApp Status: {message_sid} -> {message_status}")
    print(f"   From: {from_number} To: {to_number}")
    
    # Log status for debugging
    if message_status in ['delivered', 'read']:
        print(f"✅ Message {message_sid} {message_status}")
    elif message_status in ['failed', 'undelivered']:
        print(f"❌ Message {message_sid} {message_status}")
    
    # Return empty 200 response (Twilio expects this)
    return Response(status=200) 