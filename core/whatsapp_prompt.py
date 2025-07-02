"""
WhatsApp-specific prompt for resume review (newsletter-grounded only).
Completely rewritten to use the new newsletter-based system.
"""

import os
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from dotenv import load_dotenv

from .newsletter_manager import NewsletterManager, NewsletterChunk
from .jd_parser import JobDescriptionParser
from .relevance_scorer import RelevanceScorer

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Get configuration from environment
MAX_OUTPUT_CHAR = int(os.getenv('MAX_OUTPUT_CHAR', 1500))

class NewsletterGroundedReviewer:
    """Newsletter-grounded resume reviewer for WhatsApp."""
    
    def __init__(self):
        """Initialize the newsletter-grounded reviewer."""
        self.newsletter_manager = NewsletterManager()
        self.jd_parser = JobDescriptionParser()
        self.relevance_scorer = RelevanceScorer(self.newsletter_manager)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    def process_resume_review(self, resume_text: str, job_url: str = None) -> Dict[str, Any]:
        """
        Process a complete resume review using newsletter-grounded approach.
        
        Args:
            resume_text: The extracted resume text
            job_url: Optional job posting URL
        
        Returns:
            Dict containing review results optimized for WhatsApp
        """
        try:
            # Step 1: Parse job description if URL provided
            jd_parsed = {}
            jd_keywords = []
            
            if job_url:
                jd_parsed = self.jd_parser.parse_job_url(job_url)
                if jd_parsed.get('success'):
                    jd_keywords = self.jd_parser.extract_keywords_for_matching(jd_parsed)
                else:
                    # Handle JD parsing failure
                    return self._create_error_result("Could not parse job description from URL")
            
            # Step 2: Get relevant newsletter content
            if jd_keywords:
                relevant_chunks = self.newsletter_manager.get_relevant_content(jd_keywords, max_chunks=5)
            else:
                # If no JD, get general resume content
                general_keywords = ['resume', 'customization', 'interview', 'experience', 'skills']
                relevant_chunks = self.newsletter_manager.get_relevant_content(general_keywords, max_chunks=5)
            
            # Step 3: Calculate confidence score
            scoring_result = self.relevance_scorer.calculate_confidence_score(
                resume_text, jd_keywords, relevant_chunks
            )
            
            # Step 4: Generate review using newsletter content
            review_text = self._generate_newsletter_grounded_review(
                resume_text, jd_parsed, relevant_chunks, scoring_result
            )
            
            # Step 5: Format for WhatsApp
            formatted_review = self._format_for_whatsapp(review_text, scoring_result)
            
            return {
                'success': True,
                'review': formatted_review,
                'confidence_score': scoring_result['confidence_score'],
                'jd_info': jd_parsed,
                'newsletter_chunks_used': len(relevant_chunks),
                'scoring_details': scoring_result,
                'error': None
            }
            
        except Exception as e:
            return self._create_error_result(f"Error processing review: {str(e)}")
    
    def _generate_newsletter_grounded_review(self, resume_text: str, jd_parsed: Dict[str, Any], 
                                           newsletter_chunks: List[NewsletterChunk], 
                                           scoring_result: Dict[str, Any]) -> str:
        """
        Generate review text strictly grounded in newsletter content.
        
        Args:
            resume_text: The resume text
            jd_parsed: Parsed job description information
            newsletter_chunks: Relevant newsletter chunks
            scoring_result: Calculated scoring information
        
        Returns:
            Generated review text
        """
        # Prepare newsletter content for prompt
        newsletter_content = self._prepare_newsletter_content_for_prompt(newsletter_chunks)
        
        # Create the system prompt
        system_prompt = self._create_system_prompt()
        
        # Create the user prompt
        user_prompt = self._create_user_prompt(
            resume_text, jd_parsed, newsletter_content, scoring_result
        )
        
        try:
            # Generate with Gemini
            print(f"🤖 Calling Gemini API...")
            print(f"System prompt length: {len(system_prompt)}")
            print(f"User prompt length: {len(user_prompt)}")
            
            response = self.gemini_model.generate_content(
                f"{system_prompt}\n\n{user_prompt}"
            )
            
            print(f"✅ Gemini API call successful")
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini API call failed: {e}")
            return self._create_fallback_review(scoring_result, newsletter_chunks)
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for newsletter-grounded review."""
        return f'''You are Aakash, a resume expert and creator who helps people optimize their resumes. You ONLY provide feedback based on the newsletter content provided to you. 

CRITICAL RULES:
1. Base ALL feedback on the newsletter content provided - never use outside knowledge
2. Reference newsletter principles (not section names) in your feedback
3. If a topic isn't covered in the newsletter, explicitly state: "I haven't covered [topic] in my content yet"
4. Use Aakash's authentic creator voice and perspective as shown in the newsletter
5. Keep responses under {MAX_OUTPUT_CHAR} characters total for WhatsApp
6. Focus on actionable, specific advice from the newsletter
7. Write as if you're personally helping the user based on your newsletter expertise
8. Use phrases like "Based on my newsletter principles..." and "As I mention in my content..."
9. Do NOT show any scores or percentages to the user - use them internally only
10. Make Next Steps company-specific when job description is provided
11. Emphasize newsletter-grounded authenticity and creator expertise
12. For each section (Strengths, Areas to Improve, Next Steps), provide at least 2-3 detailed bullet points or examples, not just a summary.
13. Be as specific and actionable as possible. Give concrete suggestions and examples, not just generalities.
14. If possible, elaborate on why each suggestion matters for the target job/company.'''
    
    def _create_user_prompt(self, resume_text: str, jd_parsed: Dict[str, Any], 
                          newsletter_content: str, scoring_result: Dict[str, Any]) -> str:
        """Create the user prompt with all context information."""
        
        # Prepare JD information
        jd_info = ""
        if jd_parsed.get('success'):
            jd_info = f"""
Job Description Context:
- Role: {jd_parsed.get('role_title', 'N/A')}
- Company: {jd_parsed.get('company_name', 'N/A')}
- Key Qualifications: {jd_parsed.get('key_qualifications', 'N/A')}"""
        else:
            jd_info = "No specific job description provided - providing general resume feedback."
        
        confidence_score = scoring_result.get('confidence_score', 0)
        jd_overlap = scoring_result.get('jd_resume_overlap', 0)
        
        # Determine feedback tone based on overlap
        if jd_overlap <= 20:
            overlap_guidance = "This resume needs significant customization for this role. Focus on keyword alignment and role-specific language."
        elif jd_overlap <= 50:
            overlap_guidance = "Some alignment found, but key improvements needed. Emphasize customization and specific role requirements."
        else:
            overlap_guidance = "Good alignment found. Focus on fine-tuning and optimization."
        
        # Get company name for Next Steps
        company_name = jd_parsed.get('company_name', 'the target company') if jd_parsed.get('success') else 'the target company'
        
        return f"""
{jd_info}

Resume Text:
{resume_text}

Newsletter Content (YOUR ONLY SOURCE OF ADVICE):
{newsletter_content}

INTERNAL ANALYSIS (for your guidance only):
- JD-Resume Overlap: {jd_overlap}%
- Confidence Score: {confidence_score}/100
- Guidance: {overlap_guidance}

Please provide a resume review using ONLY the newsletter content above. Structure your response as:

1. Overall Assessment (no scores shown to user)
2. Strengths (reference newsletter principles, not section names)
3. Areas to Improve (reference newsletter principles for this role)  
4. Next Steps for {company_name} Role (provide 2-3 company-specific, actionable steps based on newsletter content)

CRITICAL INSTRUCTIONS:
- Do NOT show any scores or percentages to the user
- Keep response under {MAX_OUTPUT_CHAR} characters total
- Make Next Steps specific to {company_name} when job description is provided
- Reference newsletter principles, not section names
- Do NOT repeat generic advice - provide specific, actionable steps for {company_name}
- Use the overlap analysis internally to guide your feedback tone and focus
- Base all advice on the newsletter content provided

Remember: If something isn't covered in the newsletter content, say so explicitly."""
    
    def _prepare_newsletter_content_for_prompt(self, chunks: List[NewsletterChunk]) -> str:
        """Prepare newsletter chunks for inclusion in prompt."""
        if not chunks:
            return "No relevant newsletter content available."
        
        # Limit to 5 most relevant chunks to give the AI more material
        limited_chunks = chunks[:5]
        
        content_parts = []
        for chunk in limited_chunks:
            content_parts.append(f"## {chunk.section} (from {chunk.article_name})\n{chunk.content}")
        
        return "\n\n".join(content_parts)
    
    def _format_for_whatsapp(self, review_text: str, scoring_result: Dict[str, Any]) -> str:
        """
        Format the review text optimally for WhatsApp.
        
        Args:
            review_text: The generated review text
            scoring_result: Scoring information
        
        Returns:
            WhatsApp-optimized text
        """
        confidence_score = scoring_result.get('confidence_score', 0)
        
        # Clean up the review text
        formatted_text = self._clean_review_text(review_text)
        
        # Add WhatsApp-friendly formatting with creator context
        whatsapp_text = f"""🎯 *Resume Review by Aakash*

{formatted_text}

📚 *Based on my newsletter: How to Customize Your Resume to Actually Get Interviews*
🔗 https://www.news.aakashg.com/p/how-to-customize-your-resume-to-actually"""
        
        # No truncation - let the WhatsApp response system handle message splitting
        
        return whatsapp_text
    
    def _clean_review_text(self, text: str) -> str:
        """Clean and format review text for WhatsApp."""
        if not text:
            return "Review could not be generated from newsletter content."
        
        # Remove markdown formatting that doesn't work well in WhatsApp
        text = text.replace('**', '*')
        text = text.replace('##', '*')
        text = text.replace('###', '')
        
        # Clean up extra whitespace but preserve structure
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:  # Keep non-empty lines
                lines.append(line)
            elif lines and lines[-1]:  # Add empty line only if previous line wasn't empty
                lines.append('')
        
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()
        
        return '\n'.join(lines)
    
    def _truncate_for_whatsapp(self, text: str, max_length: int = None) -> str:
        """Generate a complete WhatsApp message that fits within limits."""
        if max_length is None:
            max_length = MAX_OUTPUT_CHAR
        
        if len(text) <= max_length:
            return text
        
        # Try to keep as many full sections as possible
        lines = text.split('\n')
        concise_lines = []
        total_length = 0
        footer = [
            '',
            '📚 *Based on my newsletter: How to Customize Your Resume to Actually Get Interviews*',
            '🔗 https://www.news.aakashg.com/p/how-to-customize-your-resume-to-actually'
        ]
        footer_length = sum(len(line) + 1 for line in footer)  # +1 for newline
        
        for line in lines:
            # Always keep the header
            if not concise_lines and "🎯 *Resume Review by Aakash*" in line:
                concise_lines.append(line)
                total_length += len(line) + 1
                continue
            # Add lines as long as we don't exceed the limit (leaving space for footer and note)
            if total_length + len(line) + 1 + footer_length + 40 < max_length:  # 40 chars for omitted note
                concise_lines.append(line)
                total_length += len(line) + 1
            else:
                break
        
        # Add omitted note if we had to truncate (only if we broke out of the loop early)
        if len(concise_lines) < len(lines):
            concise_lines.append('')
            concise_lines.append('⚠️ Some content was omitted for length.')
        
        concise_lines.extend(footer)
        return '\n'.join(concise_lines)
    
    def _create_fallback_review(self, scoring_result: Dict[str, Any], 
                              newsletter_chunks: List[NewsletterChunk]) -> str:
        """Create a fallback review when AI generation fails."""
        confidence_score = scoring_result.get('confidence_score', 0)
        
        # Get basic strengths and improvements from scoring
        basic_review = f"""Based on my newsletter content analysis:

💪 *Key Strengths:*
• Shows relevant professional experience
• Demonstrates career progression

🔧 *Areas to Improve:*
• Better keyword alignment with job requirements
• More quantified achievements

🎯 *Next Steps for the target company Role:*
• Research the target company's culture and values
• Customize experience for this specific role"""
        
        if newsletter_chunks:
            basic_review += f"\n\n📚 *Based on my newsletter: How to Customize Your Resume to Actually Get Interviews*\n🔗 https://www.news.aakashg.com/p/how-to-customize-your-resume-to-actually"
        
        return basic_review
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create an error result dictionary."""
        return {
            'success': False,
            'review': f"❌ {error_message}",
            'confidence_score': 0,
            'jd_info': {},
            'newsletter_chunks_used': 0,
            'scoring_details': {},
            'error': error_message
        }
    
    def get_fallback_message_for_topic(self, topic: str) -> str:
        """
        Get fallback message when newsletter doesn't cover a topic.
        
        Args:
            topic: The topic not covered
        
        Returns:
            Fallback message
        """
        return f"""I haven't covered {topic} in my newsletter content yet, but here's what I can help with based on my available content:

• Resume customization principles
• Job description alignment strategies  
• Experience positioning techniques
• Keyword optimization approaches

Feel free to ask about any of these areas!"""

# Legacy compatibility functions (to be removed after full migration)
def create_whatsapp_review_prompt(resume_text: str, jd_parsed: Dict[str, str] = None, 
                                newsletter_content: str = None, confidence_score: Optional[int] = None,
                                article_name: Optional[str] = None) -> Dict[str, str]:
    """
    Legacy compatibility function - redirects to new system.
    """
    reviewer = NewsletterGroundedReviewer()
    
    # Convert old parameters to new system
    job_url = None  # Old system didn't have direct URL support
    
    result = reviewer.process_resume_review(resume_text, job_url)
    
    if result['success']:
        return {
            "system": "You are Aakash providing newsletter-grounded resume feedback.",
            "user": result['review'],
            "article_name": "Newsletter-grounded review"
        }
    else:
        return {
            "system": "Error in newsletter-grounded review",
            "user": result['review'],
            "article_name": "Error"
        }

def process_whatsapp_resume_review(resume_text: str, goal: str = None) -> Dict[str, Any]:
    """
    Legacy compatibility function - redirects to new system.
    """
    reviewer = NewsletterGroundedReviewer()
    result = reviewer.process_resume_review(resume_text)
    
    # Convert to legacy format
    return {
        "success": result['success'],
        "feedback": result['review'],
        "score": result['confidence_score'] / 100.0,  # Convert to 0-1 scale
        "goal": goal or "Newsletter-grounded review",
        "creator": "Aakash",
        "newsletter_source": "https://www.news.aakashg.com/p/how-to-customize-your-resume-to-actually"
    } 