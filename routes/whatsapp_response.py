import os
import requests
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WhatsAppResponder:
    def __init__(self):
        """
        Initialize the WhatsApp responder with Twilio credentials.
        """
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        # Check if all credentials are available
        self.credentials_available = all([self.account_sid, self.auth_token, self.whatsapp_number])
        
        # Debug: Print credential status
        print(f"Twilio Debug - Account SID: {'Set' if self.account_sid else 'Missing'}")
        print(f"Twilio Debug - Auth Token: {'Set' if self.auth_token else 'Missing'}")
        print(f"Twilio Debug - WhatsApp Number: {'Set' if self.whatsapp_number else 'Missing'}")
        print(f"Twilio Debug - All credentials available: {self.credentials_available}")
        
        if self.credentials_available:
            self.client = Client(self.account_sid, self.auth_token)
            print("Twilio client initialized successfully")
        else:
            self.client = None
            print("Warning: Twilio credentials not configured. WhatsApp messages will not be sent.")
    
    def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.
        
        Args:
            to_number: The recipient's phone number (with country code)
            message: The message to send
        
        Returns:
            Dict containing success status and message details
        """
        if not self.credentials_available:
            return {
                "success": False,
                "message_sid": None,
                "status": "not_configured",
                "error": "Twilio credentials not configured"
            }
        
        try:
            # Format the number for WhatsApp
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            # Send the message
            message_obj = self.client.messages.create(
                from_=f"whatsapp:{self.whatsapp_number}",
                body=message,
                to=to_number
            )
            
            return {
                "success": True,
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "error": None
            }
            
        except TwilioException as e:
            return {
                "success": False,
                "message_sid": None,
                "status": "failed",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message_sid": None,
                "status": "failed",
                "error": f"Unexpected error: {str(e)}"
            }
    
    def send_resume_review_response(self, to_number: str, feedback: str, pdf_path: str = None, 
                                  score: float = 0.85, creator: str = "Aakash") -> Dict[str, Any]:
        """
        Send a newsletter-grounded resume review response.
        
        Args:
            to_number: The recipient's phone number
            feedback: The newsletter-grounded feedback (already formatted)
            pdf_path: Path to the generated PDF (optional, not used in new system)
            score: Confidence score of the review (0.0 to 1.0)
            creator: Name of the creator/expert
        
        Returns:
            Dict containing the response status
        """
        try:
            print(f"WhatsApp Debug - Sending newsletter-grounded review response")
            
            # Check if the feedback is already optimized for WhatsApp (from new system)
            if self._is_newsletter_grounded_format(feedback):
                # Split long messages into multiple parts if needed
                return self._send_split_messages(to_number, feedback)
            else:
                # Fall back to multi-message format for legacy feedback
                return self._send_legacy_multi_message_review(to_number, feedback, score, creator)
            
        except Exception as e:
            print(f"WhatsApp Debug - Exception in send_resume_review_response: {e}")
            return {
                "success": False,
                "single_message": None,
                "error": str(e)
            }
    
    def _is_newsletter_grounded_format(self, feedback: str) -> bool:
        """
        Check if feedback is from the new newsletter-grounded system.
        
        Args:
            feedback: The feedback text
        
        Returns:
            True if it's from the new system, False otherwise
        """
        # Check for markers of the new system (more comprehensive)
        positive_markers = [
            "🎯 *Resume Review by Aakash*",
            "📚 *Based on my newsletter:",
            "Based on my newsletter principles",
            "As I mention in my content",
            "Based on my newsletter content",
            "newsletter principles",
            "newsletter content"
        ]
        
        # Check for fallback markers that indicate the system failed
        fallback_markers = [
            "I haven't covered",
            "I haven't covered specific strengths",
            "I haven't covered specific areas",
            "I haven't covered next steps"
        ]
        
        # Check for legacy format markers
        legacy_markers = [
            "🎯 *Resume Review Complete!*",
            "Powered by Aakash's newsletter expertise",
            "📊 *Overall Assessment:*",
            "💪 *Key Strengths Identified:*"
        ]
        
        # Must have positive markers AND not be a fallback message AND not be legacy format
        has_positive_markers = any(marker in feedback for marker in positive_markers)
        is_fallback = any(marker in feedback for marker in fallback_markers)
        is_legacy = any(marker in feedback for marker in legacy_markers)
        
        return has_positive_markers and not is_fallback and not is_legacy
    
    def _send_split_messages(self, to_number: str, feedback: str) -> Dict[str, Any]:
        """
        Send long feedback by splitting into multiple messages if needed.
        
        Args:
            to_number: The recipient's phone number
            feedback: The complete feedback text
        
        Returns:
            Dict containing the response status
        """
        try:
            # WhatsApp character limit (leaving some buffer)
            max_chars = 1400
            
            if len(feedback) <= max_chars:
                # Single message is fine
                result = self.send_text_message(to_number, feedback)
                return {
                    "success": result["success"],
                    "single_message": result,
                    "error": result.get("error")
                }
            
            # Split into multiple messages
            lines = feedback.split('\n')
            messages = []
            current_message = []
            current_length = 0
            
            for line in lines:
                line_length = len(line) + 1  # +1 for newline
                
                # If adding this line would exceed limit, start a new message
                if current_length + line_length > max_chars and current_message:
                    messages.append('\n'.join(current_message))
                    current_message = [line]
                    current_length = line_length
                else:
                    current_message.append(line)
                    current_length += line_length
            
            # Add the last message
            if current_message:
                messages.append('\n'.join(current_message))
            
            # Send all messages
            results = []
            for i, message in enumerate(messages):
                if i > 0:
                    # Add message number for multi-part messages
                    message = f"(Part {i+1}/{len(messages)})\n\n{message}"
                
                result = self.send_text_message(to_number, message)
                results.append(result)
                
                # Small delay between messages
                import time
                time.sleep(0.5)
            
            # Check if all messages were sent successfully
            all_success = all(result["success"] for result in results)
            
            return {
                "success": all_success,
                "split_messages": results,
                "message_count": len(messages),
                "error": None if all_success else "Some messages failed to send"
            }
            
        except Exception as e:
            print(f"WhatsApp Debug - Exception in _send_split_messages: {e}")
            return {
                "success": False,
                "split_messages": None,
                "error": str(e)
            }
    
    def _send_legacy_multi_message_review(self, to_number: str, feedback: str, 
                                        score: float, creator: str) -> Dict[str, Any]:
        """
        Send legacy multi-message review format.
        
        Args:
            to_number: The recipient's phone number
            feedback: The AI-generated feedback
            score: Confidence score
            creator: Name of the creator
        
        Returns:
            Dict containing the response status
        """
        try:
            # Message 1: Overview & Assessment
            overview_message = self._create_overview_message(feedback, score, creator)
            overview_result = self.send_text_message(to_number, overview_message)
            if not overview_result["success"]:
                return overview_result
            
            # Message 2: Insights & Recommendations
            insights_message = self._create_insights_recommendations_message(feedback)
            insights_result = self.send_text_message(to_number, insights_message)
            
            return {
                "success": True,
                "overview_message": overview_result,
                "insights_message": insights_result,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "overview_message": None,
                "insights_message": None,
                "error": str(e)
            }
    
    def send_error_message(self, to_number: str, error_type: str, details: str = None) -> Dict[str, Any]:
        """
        Send an error message to the user.
        
        Args:
            to_number: The recipient's phone number
            error_type: Type of error (e.g., 'invalid_resume', 'processing_error')
            details: Additional error details
        
        Returns:
            Dict containing the response status
        """
        error_messages = {
            'invalid_resume': "❌ Sorry! I couldn't process your resume. Please make sure it's a valid PDF file and try again.",
            'unsupported_format': "❌ I only support PDF resumes at the moment. Please convert your file to PDF and try again.",
            'processing_error': "❌ Something went wrong while processing your resume. Please try again in a few minutes.",
            'invalid_job_url': "❌ I couldn't extract information from that job URL. Please check the link and try again.",
            'low_confidence': "⚠️ Here are some general tips based on my newsletter:\n\n• Focus on quantifiable achievements\n• Use action verbs and specific metrics\n• Tailor keywords to the job description\n• Keep bullets concise and impactful",
            'file_too_large': "❌ Your resume file is too large. Please compress it to under 10MB and try again.",
            'rate_limit': "⏰ I'm processing too many requests right now. Please try again in a few minutes.",
            'newsletter_unavailable': "❌ My newsletter content is temporarily unavailable. Please try again later.",
            'jd_parsing_failed': "⚠️ I couldn't parse the job description, but I'll provide general feedback based on my newsletter content."
        }
        
        message = error_messages.get(error_type, "❌ An unexpected error occurred. Please try again.")
        
        if details and error_type in ['processing_error', 'newsletter_unavailable']:
            message += f"\n\nDetails: {details[:100]}..."
        
        return self.send_text_message(to_number, message)
    
    def _create_overview_message(self, feedback: str, score: float, creator: str) -> str:
        """
        Create the overview and assessment message for legacy format.
        
        Args:
            feedback: The AI-generated feedback
            score: Confidence score (0.0 to 1.0)
            creator: Name of the creator
        
        Returns:
            Formatted overview message
        """
        sections = self._extract_feedback_sections(feedback)
        
        message = f"🎯 *Resume Review Complete!*\n\n"
        message += f"Powered by {creator}'s newsletter expertise\n\n"
        
        # Add overall assessment
        if sections.get('assessment'):
            assessment = sections['assessment'][0] if sections['assessment'] else ""
            if len(assessment) > 300:
                assessment = assessment[:297] + "..."
            message += f"📊 *Overall Assessment:*\n{assessment}\n\n"
        else:
            message += "📊 *Overall Assessment:*\nYour resume has been analyzed using proven optimization principles.\n\n"
        
        message += "💪 *Key Strengths Identified:*\n"
        # Extract strengths from the feedback
        strengths = self._extract_strengths(feedback)
        if strengths:
            for strength in strengths[:3]:
                if len(strength) > 150:
                    strength = strength[:147] + "..."
                message += f"• {strength}\n"
        else:
            message += "• Strong experience in relevant areas\n"
            message += "• Good foundation for optimization\n"
        
        message += "\n🔗 *Source:* Based on proven resume optimization principles."
        
        # Ensure message doesn't exceed 1600 characters
        if len(message) > 1600:
            message = message[:1597] + "..."
        
        return message
    
    def _extract_feedback_sections(self, feedback: str) -> Dict[str, list]:
        """
        Extract key sections from the feedback for the WhatsApp message.
        
        Args:
            feedback: The full feedback text
        
        Returns:
            Dict containing extracted sections
        """
        sections = {
            'assessment': [],
            'improvements': [],
            'bullets': [],
            'tips': []
        }
        
        lines = feedback.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Detect sections
            if 'overall assessment' in line.lower() or 'overall fit' in line.lower():
                current_section = 'assessment'
                continue
            elif 'improvements needed' in line.lower() or 'areas to improve' in line.lower():
                current_section = 'improvements'
                continue
            elif 'rewritten bullets' in line.lower() or 'improved bullets' in line.lower():
                current_section = 'bullets'
                continue
            elif 'role-specific tips' in line.lower() or 'next steps' in line.lower():
                current_section = 'tips'
                continue
            elif line.startswith('##') or line.startswith('**'):
                current_section = None
                continue
            
            # Add content to current section
            if current_section and line and len(line) > 10:
                # Clean up bullet points
                clean_line = line.lstrip('•-*→➤')
                clean_line = clean_line.strip()
                
                if clean_line:
                    sections[current_section].append(clean_line)
        
        return sections
    
    def _create_insights_recommendations_message(self, feedback: str) -> str:
        """
        Create the insights and recommendations message for legacy format.
        
        Args:
            feedback: The AI-generated feedback
        
        Returns:
            Formatted insights and recommendations message
        """
        sections = self._extract_feedback_sections(feedback)
        
        message = "📊 *Key Insights & Recommendations:*\n\n"
        
        # Add areas for improvement
        if sections.get('improvements'):
            message += "🔧 *Areas for Improvement:*\n"
            for i, improvement in enumerate(sections['improvements'][:4], 1):
                if len(improvement) > 200:
                    improvement = improvement[:197] + "..."
                message += f"{i}. {improvement}\n"
            message += "\n"
        else:
            message += "🔧 *Areas for Improvement:*\n"
            message += "1. Add more quantifiable metrics to bullet points\n"
            message += "2. Include specific outcomes and impact\n"
            message += "3. Tailor keywords to target roles\n"
            message += "4. Highlight leadership and strategic thinking\n\n"
        
        # Add actionable recommendations
        message += "💡 *Actionable Recommendations:*\n"
        recommendations = self._extract_recommendations(feedback)
        if recommendations:
            for rec in recommendations[:4]:
                if len(rec) > 150:
                    rec = rec[:147] + "..."
                message += f"• {rec}\n"
        else:
            message += "• Focus on quantifiable achievements (%, $, numbers)\n"
            message += "• Use action verbs and specific metrics\n"
            message += "• Tailor keywords to the job description\n"
            message += "• Keep bullets concise and impactful\n"
        
        message += "\n🎯 *Next Steps:*\n"
        message += "• Apply these insights to your resume\n"
        message += "• Focus on the most impactful improvements first\n"
        message += "• Consider role-specific customization\n"
        
        # Add newsletter attribution
        message += "\n📚 *Based on newsletter best practices*"
        
        # Ensure message doesn't exceed 1600 characters
        if len(message) > 1600:
            message = message[:1597] + "..."
        
        return message
    
    def _extract_strengths(self, feedback: str) -> list:
        """
        Extract strengths from the feedback.
        
        Args:
            feedback: The AI-generated feedback
        
        Returns:
            List of strengths
        """
        strengths = []
        lines = feedback.split('\n')
        
        for line in lines:
            line = line.strip().lower()
            if any(word in line for word in ['strong', 'excellent', 'good', 'solid', 'impressive', 'notable', 'strength']):
                # Look for the next few lines for context
                original_line = lines[lines.index(line.strip()) if line.strip() in lines else 0]
                if len(original_line.strip()) > 20:
                    strengths.append(original_line.strip())
        
        return strengths[:3]  # Limit to 3 strengths
    
    def _extract_recommendations(self, feedback: str) -> list:
        """
        Extract actionable recommendations from the feedback.
        
        Args:
            feedback: The AI-generated feedback
        
        Returns:
            List of recommendations
        """
        recommendations = []
        lines = feedback.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(word in line.lower() for word in ['recommend', 'suggest', 'consider', 'focus on', 'improve', 'enhance']):
                if len(line) > 20:
                    recommendations.append(line)
        
        return recommendations[:4]  # Limit to 4 recommendations

def send_whatsapp_response(to_number: str, feedback: str, pdf_path: str = None, 
                          score: float = 0.85, creator: str = "Aakash") -> Dict[str, Any]:
    """
    Convenience function to send a WhatsApp response.
    
    Args:
        to_number: The recipient's phone number
        feedback: The AI-generated feedback (newsletter-grounded or legacy)
        pdf_path: Path to the generated PDF (optional, not used in new system)
        score: Confidence score (0.0 to 1.0)
        creator: Name of the creator
    
    Returns:
        Dict containing the response status
    """
    try:
        print(f"WhatsApp Response Debug - Starting for phone: {to_number}")
        responder = WhatsAppResponder()
        print(f"WhatsApp Response Debug - Credentials available: {responder.credentials_available}")
        
        result = responder.send_resume_review_response(to_number, feedback, pdf_path, score, creator)
        print(f"WhatsApp Response Debug - Result: {result}")
        
        # If credentials are not configured, still return success but indicate WhatsApp wasn't sent
        if not responder.credentials_available:
            result["success"] = True  # API call was successful
            result["whatsapp_configured"] = False
            result["message"] = "Resume processed successfully. WhatsApp not configured."
            print("WhatsApp Response Debug - Credentials not available, returning fallback response")
        
        return result
    except Exception as e:
        print(f"WhatsApp Response Debug - Exception: {e}")
        return {
            "success": False,
            "error": str(e)
        } 