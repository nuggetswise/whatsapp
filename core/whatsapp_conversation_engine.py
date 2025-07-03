"""WhatsApp Conversation Engine - Core Logic for Progressive Resume Review

This module implements the stateless conversation flow for WhatsApp resume reviews.
It handles progressive disclosure, interactive choices, and state management.

Key Principles:
- Stateless: All state is passed in/out, no internal state
- Portable: No dependencies on Flask, Twilio, or other frameworks
- Testable: Pure functions that can be unit tested
- Modular: Clear separation of concerns
"""

from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
from datetime import datetime


class ConversationStep(Enum):
    """Enumeration of conversation steps for state management"""
    INITIAL = "initial"
    SUMMARY_SENT = "summary_sent"
    AWAITING_CHOICE = "awaiting_choice"
    SKILLS_DETAIL = "skills_detail"
    EXPERIENCE_DETAIL = "experience_detail"
    FORMATTING_DETAIL = "formatting_detail"
    COMPLETE_REVIEW = "complete_review"
    ENGAGEMENT_QUESTION = "engagement_question"
    AWAITING_CONCERN = "awaiting_concern"
    FINAL_ADVICE = "final_advice"


class ConversationEngine:
    """Core conversation engine for WhatsApp resume reviews"""
    
    def __init__(self):
        self.max_message_length = 1000  # WhatsApp recommended limit
        
    def start_conversation(self, 
                          user_name: str,
                          resume_data: Dict[str, Any],
                          job_data: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Start a new conversation with executive summary
        
        Args:
            user_name: User's name for personalization
            resume_data: Resume analysis results
            job_data: Optional job description data
            
        Returns:
            Tuple of (messages_to_send, new_state)
        """
        # Create initial state
        state = {
            "step": ConversationStep.SUMMARY_SENT.value,
            "user_name": user_name,
            "resume_data": resume_data,
            "job_data": job_data,
            "conversation_start": datetime.now().isoformat(),
            "message_count": 0,
            "last_choice": None,
            "engagement_history": []
        }
        
        # Generate executive summary message
        summary_message = self._create_executive_summary(user_name, resume_data, job_data)
        
        messages = [{
            "type": "text",
            "content": summary_message,
            "quick_replies": self._get_choice_quick_replies()
        }]
        
        return messages, state
    
    def continue_conversation(self, 
                            user_input: str, 
                            current_state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Continue conversation based on user input and current state
        
        Args:
            user_input: User's message/choice
            current_state: Current conversation state
            
        Returns:
            Tuple of (messages_to_send, updated_state)
        """
        # Update state
        state = current_state.copy()
        state["message_count"] += 1
        state["last_input"] = user_input
        state["last_input_time"] = datetime.now().isoformat()
        
        current_step = ConversationStep(state.get("step", ConversationStep.INITIAL.value))
        
        # Route based on current step and user input
        if current_step == ConversationStep.SUMMARY_SENT:
            return self._handle_choice_response(user_input, state)
        elif current_step == ConversationStep.AWAITING_CHOICE:
            return self._handle_choice_response(user_input, state)
        elif current_step in [ConversationStep.SKILLS_DETAIL, 
                             ConversationStep.EXPERIENCE_DETAIL, 
                             ConversationStep.FORMATTING_DETAIL,
                             ConversationStep.COMPLETE_REVIEW]:
            return self._handle_detail_followup(user_input, state)
        elif current_step == ConversationStep.ENGAGEMENT_QUESTION:
            return self._handle_engagement_response(user_input, state)
        elif current_step == ConversationStep.AWAITING_CONCERN:
            return self._handle_concern_response(user_input, state)
        else:
                         # Fallback for unexpected states
             return self._handle_fallback(user_input, state)
    
    def _create_executive_summary(self, 
                                 user_name: str, 
                                 resume_data: Dict[str, Any], 
                                 job_data: Optional[Dict[str, Any]] = None) -> str:
        """Create executive summary message"""
        job_title = job_data.get("title", "this role") if job_data else "this role"
        company = job_data.get("company", "the company") if job_data else "the company"
        
        # Extract key metrics from resume_data
        strengths = resume_data.get("strengths", [])
        improvements = resume_data.get("improvements", [])
        confidence = resume_data.get("confidence_score", 0)
        
        summary = f"""🎯 Resume Review by Aakash

Hey {user_name}! I analyzed your resume for the {job_title} role at {company}.

📊 Quick Overview:"""
        
        # Add strengths (limit to 2-3 key ones)
        if strengths:
            summary += "\n✅ " + "\n✅ ".join(strengths[:3])
        
        # Add improvements (limit to 2-3 key ones)
        if improvements:
            summary += "\n⚠️ " + "\n⚠️ ".join(improvements[:3])
        
        # Add confidence indicator
        if confidence > 0:
            confidence_text = self._get_confidence_text(confidence)
            summary += f"\n\nConfidence: {confidence_text}"
        
        summary += "\n\nWhat would you like me to dive deeper into?"
        
        return summary
    
    def _get_choice_quick_replies(self) -> List[Dict[str, str]]:
        """Get quick reply options for user choice"""
        return [
            {"id": "1", "title": "Skills & Keywords"},
            {"id": "2", "title": "Experience & Achievements"},
            {"id": "3", "title": "Formatting & ATS"},
            {"id": "4", "title": "All Areas (Complete Review)"}
        ]
    
    def _handle_choice_response(self, 
                               user_input: str, 
                               state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Handle user's choice of what to focus on"""
        choice_map = {
            "1": "skills",
            "2": "experience", 
            "3": "formatting",
            "4": "complete",
            "skills": "skills",
            "experience": "experience",
            "formatting": "formatting",
            "complete": "complete"
        }
        
        choice = choice_map.get(user_input.lower().strip(), "complete")
        state["last_choice"] = choice
        state["step"] = ConversationStep.AWAITING_CHOICE.value
        
        messages = []
        
        if choice == "skills":
            messages.append({
                "type": "text",
                "content": self._create_skills_detail_message(state)
            })
            state["step"] = ConversationStep.SKILLS_DETAIL.value
            
        elif choice == "experience":
            messages.append({
                "type": "text", 
                "content": self._create_experience_detail_message(state)
            })
            state["step"] = ConversationStep.EXPERIENCE_DETAIL.value
            
        elif choice == "formatting":
            messages.append({
                "type": "text",
                "content": self._create_formatting_detail_message(state)
            })
            state["step"] = ConversationStep.FORMATTING_DETAIL.value
            
        elif choice == "complete":
            messages.extend(self._create_complete_review_messages(state))
            state["step"] = ConversationStep.COMPLETE_REVIEW.value
        
        # Add engagement question
        engagement_message = self._create_engagement_question(state)
        if engagement_message:
            messages.append({
                "type": "text",
                "content": engagement_message,
                "quick_replies": self._get_concern_quick_replies()
            })
            state["step"] = ConversationStep.ENGAGEMENT_QUESTION.value
        
        return messages, state


    def _create_skills_detail_message(self, state: Dict[str, Any]) -> str:
        """Create detailed skills analysis message"""
        resume_data = state.get("resume_data", {})
        job_data = state.get("job_data", {})
        
        matching_keywords = resume_data.get("matching_keywords", [])
        missing_keywords = resume_data.get("missing_keywords", [])
        
        message = "🎯 Skills & Keywords Analysis\n\n"
        
        if matching_keywords:
            message += f"✅ MATCHING: {', '.join(matching_keywords[:3])}\n"
        
        if missing_keywords:
            message += f"❌ MISSING: {', '.join(missing_keywords[:5])}\n"
        
        message += "\n📚 Newsletter Insight:\n"
        message += "As I mention in my newsletter, \"Keywords are your resume's currency.\" "
        message += f"You're missing {len(missing_keywords)} key requirements for this role.\n\n"
        
        message += "🎯 Action Plan:\n"
        for i, keyword in enumerate(missing_keywords[:3], 1):
            message += f"{i}. Add \"{keyword}\" to skills section\n"
        
        message += "\nWant me to show you exactly how to add these? Reply \"YES\" for specific examples!"
        
        return message
    
    def _create_experience_detail_message(self, state: Dict[str, Any]) -> str:
        """Create detailed experience analysis message"""
        resume_data = state.get("resume_data", {})
        achievements = resume_data.get("quantified_achievements", [])
        
        message = "💼 Experience & Achievements Analysis\n\n"
        
        if achievements:
            message += f"📊 Quantified Achievements Found: {len(achievements)}\n"
            for achievement in achievements[:3]:
                message += f"✅ \"{achievement}\"\n"
        
        message += "\n📚 Newsletter Insight:\n"
        message += "Your achievements are good, but as I write in my newsletter, "
        message += "\"Strategic impact trumps tactical wins.\" Need more enterprise-level examples.\n\n"
        
        message += "🎯 Missing Strategic Examples:\n"
        strategic_examples = ["Multi-phase project leadership", "Cross-functional team management", 
                            "Enterprise software implementation"]
        for example in strategic_examples:
            message += f"• {example}\n"
        
        message += "\nWant specific examples of how to rewrite your bullet points? Reply \"EXAMPLES\"!"
        
        return message
    
    def _create_formatting_detail_message(self, state: Dict[str, Any]) -> str:
        """Create detailed formatting analysis message"""
        resume_data = state.get("resume_data", {})
        
        message = "📄 Formatting & ATS Analysis\n\n"
        
        # Extract formatting insights from resume_data
        formatting_issues = resume_data.get("formatting_issues", [])
        ats_score = resume_data.get("ats_score", 0)
        
        if ats_score > 0:
            message += f"📊 ATS Compatibility: {ats_score}/10\n"
        
        if formatting_issues:
            message += "\n⚠️ Formatting Issues:\n"
            for issue in formatting_issues[:3]:
                message += f"• {issue}\n"
        else:
            message += "✅ Clean, professional formatting\n"
        
        message += "\n📚 Newsletter Insight:\n"
        message += "As I emphasize in my newsletter, \"ATS systems are your first interviewer.\" "
        message += "Proper formatting ensures your resume gets past the initial screening.\n\n"
        
        message += "🎯 Quick Fixes:\n"
        message += "1. Use standard fonts (Arial, Calibri)\n"
        message += "2. Avoid tables and complex layouts\n"
        message += "3. Use bullet points consistently\n"
        
        return message
    
    def _create_complete_review_messages(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create complete review messages (split into multiple if needed)"""
        resume_data = state.get("resume_data", {})
        
        # Create comprehensive review content
        review_content = self._create_comprehensive_review_content(state)
        
        # Split into multiple messages if needed
        messages = []
        chunks = self._split_message_into_chunks(review_content, self.max_message_length)
        
        for i, chunk in enumerate(chunks):
            messages.append({
                "type": "text",
                "content": chunk
            })
        
        return messages
    
    def _create_comprehensive_review_content(self, state: Dict[str, Any]) -> str:
        """Create comprehensive review content"""
        resume_data = state.get("resume_data", {})
        job_data = state.get("job_data", {})
        
        content = "🎯 Complete Resume Review by Aakash\n\n"
        
        # Add all sections
        content += self._create_skills_detail_message(state) + "\n\n"
        content += self._create_experience_detail_message(state) + "\n\n"
        content += self._create_formatting_detail_message(state) + "\n\n"
        
        # Add action items
        content += "📈 Action Items:\n\n"
        content += "1. IMMEDIATE (This Week):\n"
        content += "   • Add missing keywords to skills\n"
        content += "   • Strengthen 2-3 strategic bullet points\n\n"
        
        content += "2. SHORT-TERM (Next 2 Weeks):\n"
        content += "   • Improve stakeholder management stories\n"
        content += "   • Optimize formatting for ATS\n\n"
        
        content += "3. ONGOING:\n"
        content += "   • Track application success rates\n"
        content += "   • Update based on feedback\n\n"
        
        content += "Need help with any of these areas? Just reply with your questions!"
        
        return content
    
    def _create_engagement_question(self, state: Dict[str, Any]) -> Optional[str]:
        """Create engagement question to keep conversation going"""
        return """🎯 Quick Question:

What's your biggest concern about this resume?

A) Getting past ATS screening
B) Standing out in interviews  
C) Matching the job requirements
D) Formatting and presentation

This will help me give you more targeted advice! 🎯"""
    
    def _get_concern_quick_replies(self) -> List[Dict[str, str]]:
        """Get quick reply options for concern question"""
        return [
            {"id": "A", "title": "ATS Screening"},
            {"id": "B", "title": "Interview Standing Out"},
            {"id": "C", "title": "Job Requirements"},
            {"id": "D", "title": "Formatting"}
        ]
    
    def _handle_engagement_response(self, 
                                   user_input: str, 
                                   state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Handle user's response to engagement question"""
        concern_map = {
            "a": "ats",
            "b": "interview", 
            "c": "requirements",
            "d": "formatting",
            "ats": "ats",
            "interview": "interview",
            "requirements": "requirements",
            "formatting": "formatting"
        }
        
        concern = concern_map.get(user_input.lower().strip(), "general")
        state["user_concern"] = concern
        state["step"] = ConversationStep.AWAITING_CONCERN.value
        
        # Create targeted advice based on concern
        advice_message = self._create_targeted_advice(concern, state)
        
        messages = [{
            "type": "text",
            "content": advice_message
        }]
        
        return messages, state
    
    def _create_targeted_advice(self, concern: str, state: Dict[str, Any]) -> str:
        """Create targeted advice based on user's concern"""
        if concern == "ats":
            return """🎯 ATS Screening Strategy

📚 Newsletter Insight: "ATS systems scan for keywords, not creativity."

🎯 Key Actions:
1. Add exact job title keywords to your resume
2. Use standard section headers (Experience, Skills, Education)
3. Avoid graphics, tables, and fancy formatting
4. Include both acronyms and full terms (e.g., "API" and "Application Programming Interface")

💡 Pro Tip: Use the job description as your keyword guide!"""
        
        elif concern == "interview":
            return """🎯 Interview Standing Out Strategy

📚 Newsletter Insight: "Your resume should tell stories that interviewers want to explore."

🎯 Key Actions:
1. Include specific metrics and outcomes
2. Add "so what?" context to achievements
3. Prepare STAR method examples for each bullet point
4. Research company culture and values

💡 Pro Tip: Every bullet point should answer "What problem did I solve?"""
        
        elif concern == "requirements":
            return """🎯 Job Requirements Matching

📚 Newsletter Insight: "Customize your resume for each role, not each company."

🎯 Key Actions:
1. Mirror the job description language
2. Prioritize relevant experience at the top
3. Add transferable skills that apply to the role
4. Quantify achievements that match job scope

💡 Pro Tip: Use the job requirements as your resume outline!"""
        
        elif concern == "formatting":
            return """🎯 Formatting & Presentation

📚 Newsletter Insight: "Professional formatting builds trust before anyone reads a word."

🎯 Key Actions:
1. Use consistent spacing and alignment
2. Choose readable fonts (Arial, Calibri, Times New Roman)
3. Use bullet points for easy scanning
4. Keep sections clearly separated

💡 Pro Tip: Print your resume to check how it looks on paper!"""
        
        else:
            return """🎯 General Resume Strategy

📚 Newsletter Insight: "Your resume is a marketing document, not a biography."

🎯 Key Actions:
1. Focus on achievements, not just responsibilities
2. Use action verbs to start bullet points
3. Quantify results whenever possible
4. Keep it concise and scannable

💡 Pro Tip: Ask yourself "Would this bullet point help me get an interview?"""

    def _handle_detail_followup(self, 
                                user_input: str, 
                                state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Handle follow-up responses in detail sections"""
        user_input_lower = user_input.lower().strip()
        
        if user_input_lower in ["yes", "examples", "show me"]:
            # Provide specific examples
            examples_message = self._create_specific_examples(state)
            return [{"type": "text", "content": examples_message}], state
        else:
            # Default to engagement question
            return self._handle_engagement_response("general", state)
    
    def _create_specific_examples(self, state: Dict[str, Any]) -> str:
        """Create specific examples based on the last choice"""
        last_choice = state.get("last_choice", "complete")
        
        if last_choice == "skills":
            return """📝 Specific Skills Examples:

BEFORE: "Experienced with various technologies"

AFTER: "Proficient in Python, React, AWS, and Docker with 3+ years building scalable web applications"

🎯 How to add:
1. Replace generic terms with specific technologies
2. Include years of experience
3. Add context about how you used them
4. Match the job description keywords exactly

💡 Pro Tip: Use the exact technology names from the job posting!"""
        
        elif last_choice == "experience":
            return """📝 Specific Experience Examples:

BEFORE: "Managed team projects"

AFTER: "Led cross-functional team of 8 engineers and designers to deliver mobile app with 50K+ downloads, resulting in 25% increase in user engagement"

🎯 How to rewrite:
1. Start with strong action verb
2. Include team size and composition
3. Add specific metrics and outcomes
4. Connect to business impact

💡 Pro Tip: Every bullet should answer "What did I accomplish?"""
        
        else:
            return """📝 General Improvement Examples:

🎯 Before vs After Examples:

BEFORE: "Responsible for project management"
AFTER: "Managed 5 concurrent projects with $2M budget, delivering 3 months ahead of schedule"

BEFORE: "Good communication skills"
AFTER: "Presented quarterly results to C-suite executives, influencing $500K budget allocation"

💡 Key Principles:
1. Quantify everything possible
2. Use specific numbers and metrics
3. Focus on outcomes, not just activities
4. Match the job description language"""

    def _handle_concern_response(self, 
                                 user_input: str, 
                                 state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Handle user's concern response"""
        # This is already handled in _handle_engagement_response
        return self._handle_engagement_response(user_input, state)
    
    def _handle_fallback(self, 
                         user_input: str, 
                         state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Handle unexpected inputs or states"""
        fallback_message = """I'm here to help with your resume review! 

You can:
• Ask for specific examples
• Get more detailed feedback
• Ask about any resume concerns

What would you like to focus on?"""
        
        return [{"type": "text", "content": fallback_message}], state
    
    def _get_confidence_text(self, confidence: float) -> str:
        """Convert confidence score to user-friendly text"""
        if confidence >= 8:
            return "8/10 - Strong match, minor improvements needed"
        elif confidence >= 6:
            return "7/10 - Good foundation, needs customization"
        elif confidence >= 4:
            return "5/10 - Some alignment, significant improvements needed"
        else:
            return "3/10 - Needs major customization for this role"
    
    def _split_message_into_chunks(self, message: str, max_length: int) -> List[str]:
        """Split long message into chunks that fit WhatsApp limits"""
        if len(message) <= max_length:
            return [message]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in message.split('\n\n'):
            if len(current_chunk) + len(paragraph) + 2 <= max_length:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


# Convenience functions for external use
def start_conversation(user_name: str, 
                      resume_data: Dict[str, Any], 
                      job_data: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Start a new conversation"""
    engine = ConversationEngine()
    return engine.start_conversation(user_name, resume_data, job_data)


def continue_conversation(user_input: str, 
                         current_state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Continue an existing conversation"""
    engine = ConversationEngine()
    return engine.continue_conversation(user_input, current_state)
