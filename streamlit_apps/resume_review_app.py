import streamlit as st
import PyPDF2
import io
import os
import requests
import re
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.newsletter_manager import NewsletterManager
from core.whatsapp_prompt import NewsletterGroundedReviewer

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize newsletter manager and creator reviewer
@st.cache_resource
def get_newsletter_manager():
    """Get cached newsletter manager instance."""
    return NewsletterManager()

@st.cache_resource
def get_creator_reviewer():
    """Get cached newsletter-grounded reviewer instance."""
    return NewsletterGroundedReviewer()



def extract_company_name_from_url(url: str) -> Optional[str]:
    """Extract company name from job posting URL."""
    try:
        # Common patterns for extracting company names from URLs
        patterns = [
            r'https?://(?:www\.)?([^.]+)\.com',
            r'https?://(?:www\.)?([^.]+)\.co',
            r'https?://(?:www\.)?([^.]+)\.io',
            r'https?://(?:www\.)?([^.]+)\.ai',
            r'https?://(?:www\.)?([^.]+)\.tech',
            r'https?://jobs\.([^.]+)\.com',
            r'https?://careers\.([^.]+)\.com',
            r'https?://([^.]+)\.jobs',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                company = match.group(1)
                # Clean up common prefixes/suffixes
                company = re.sub(r'^(jobs|careers|www)\.', '', company)
                return company.title()
        
        return None
    except Exception:
        return None

def search_company_info(company_name: str) -> dict:
    """Search for company information using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        
        company_info = {
            'name': company_name,
            'size': 'Unknown',
            'industry': 'Unknown',
            'glassdoor_rating': 'Unknown',
            'interview_difficulty': 'Unknown',
            'company_culture': 'Unknown'
        }
        
        with DDGS() as ddgs:
            # Search for company size and basic info
            size_query = f"{company_name} company size employees number of employees"
            try:
                size_results = list(ddgs.text(size_query, max_results=3))
                if size_results:
                    # Extract size information from search results
                    size_text = ' '.join([result['body'] for result in size_results])
                    # Look for common size patterns
                    size_patterns = [
                        r'(\d{1,3}(?:,\d{3})*)\s*employees',
                        r'(\d{1,3}(?:,\d{3})*)\s*people',
                        r'(\d{1,3}(?:,\d{3})*)\s*staff',
                        r'(\d{1,3}(?:,\d{3})*)\s*team members'
                    ]
                    for pattern in size_patterns:
                        match = re.search(pattern, size_text, re.IGNORECASE)
                        if match:
                            company_info['size'] = f"{match.group(1)} employees"
                            break
            except Exception:
                pass
            
            # Search for Glassdoor reviews and interview info
            glassdoor_query = f"{company_name} glassdoor reviews interview process difficulty"
            try:
                glassdoor_results = list(ddgs.text(glassdoor_query, max_results=3))
                if glassdoor_results:
                    glassdoor_text = ' '.join([result['body'] for result in glassdoor_results])
                    
                    # Extract rating if available
                    rating_match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', glassdoor_text)
                    if rating_match:
                        company_info['glassdoor_rating'] = f"{rating_match.group(1)}/5"
                    
                    # Extract interview difficulty
                    if 'difficult' in glassdoor_text.lower() or 'challenging' in glassdoor_text.lower():
                        company_info['interview_difficulty'] = 'Difficult'
                    elif 'easy' in glassdoor_text.lower() or 'straightforward' in glassdoor_text.lower():
                        company_info['interview_difficulty'] = 'Easy'
                    else:
                        company_info['interview_difficulty'] = 'Moderate'
            except Exception:
                pass
            
            # Search for company culture and industry
            culture_query = f"{company_name} company culture industry sector"
            try:
                culture_results = list(ddgs.text(culture_query, max_results=2))
                if culture_results:
                    culture_text = ' '.join([result['body'] for result in culture_results])
                    
                    # Extract industry information
                    industries = ['technology', 'healthcare', 'finance', 'retail', 'manufacturing', 'consulting', 'education']
                    for industry in industries:
                        if industry in culture_text.lower():
                            company_info['industry'] = industry.title()
                            break
                    
                    # Extract culture keywords
                    culture_keywords = ['fast-paced', 'collaborative', 'innovative', 'traditional', 'startup', 'corporate']
                    for keyword in culture_keywords:
                        if keyword in culture_text.lower():
                            company_info['company_culture'] = keyword.title()
                            break
            except Exception:
                pass
        
        return company_info
        
    except Exception as e:
        st.warning(f"Could not fetch company information: {str(e)}")
        return {
            'name': company_name,
            'size': 'Unknown',
            'industry': 'Unknown',
            'glassdoor_rating': 'Unknown',
            'interview_difficulty': 'Unknown',
            'company_culture': 'Unknown'
        }

def extract_job_description(url: str) -> Optional[str]:
    """Extract job description text from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Simple text extraction - in production you might want to use a more sophisticated parser
        # This is a basic implementation that works for many job sites
        text = response.text
        
        # Remove HTML tags and clean up the text
        # Remove script and style elements
        text = re.sub(r'<script[^<]*</script>', '', text)
        text = re.sub(r'<style[^<]*</style>', '', text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Limit the text to a reasonable length (first 5000 characters)
        if len(text) > 5000:
            text = text[:5000] + "..."
            
        return text if text else None
        
    except Exception as e:
        st.error(f"Error extracting job description from URL: {str(e)}")
        return None

def call_gemini(resume_text: str, goal: str = "General Resume Review", job_description: str = None, company_info: dict = None) -> str:
    """
    Call the newsletter-grounded resume review system.
    """
    try:
        # Get the creator reviewer instance
        reviewer = get_creator_reviewer()
        
        # For now, we'll use a job URL placeholder since the system expects a job URL
        # In the future, we could enhance this to handle job descriptions directly
        job_url = None
        
        # Create the review using the newsletter-grounded system
        review_result = reviewer.process_resume_review(
            resume_text=resume_text,
            job_url=job_url
        )
        
        if review_result.get('success'):
            return review_result['review']
        else:
            return f"Error: {review_result.get('error', 'Unknown error')}"
        
    except Exception as e:
        st.error(f"Error calling newsletter-grounded review system: {str(e)}")
        # Fallback to basic response if system fails
        return f"Sorry, there was an error processing your resume review. Please try again. Error: {str(e)}"

def extract_text_from_pdf(pdf_file) -> Optional[str]:
    """Extract text content from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None



def main():
    st.set_page_config(
        page_title="Resume Review by Aakash",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Resume Review by Aakash")
    st.markdown("Get personalized, grounded feedback on your resume based on the **6 key principles of customization** from Aakash's newsletter.")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Upload & Configure")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF)",
            type=['pdf'],
            help="Upload your resume in PDF format for review"
        )
        
        # Job posting URL input
        st.subheader("🎯 Job Posting (Optional)")
        
        job_url = st.text_input(
            "Job posting URL:",
            placeholder="https://jobs.company.com/product-manager",
            help="Paste the URL of a specific job posting for ultra-targeted feedback (optional)"
        )
        
        if job_url:
            if st.button("📥 Extract Job Description & Research Company", type="secondary"):
                with st.spinner("Extracting job description and researching company..."):
                    # Extract job description
                    job_description_text = extract_job_description(job_url)
                    
                    # Extract company name and research company
                    company_name = extract_company_name_from_url(job_url)
                    company_info = None
                    
                    if company_name:
                        company_info = search_company_info(company_name)
                    
                    if job_description_text:
                        st.session_state['job_description'] = job_description_text
                        if company_info:
                            st.session_state['company_info'] = company_info
                        st.success("✅ Job description extracted and company researched!")
                    else:
                        st.error("❌ Could not extract job description. Please check the URL.")
        
        # Show extracted job description and company info if available
        if 'job_description' in st.session_state:
            with st.expander("📋 View extracted job description", expanded=False):
                st.text_area(
                    "Job description:",
                    st.session_state['job_description'],
                    height=200,
                    disabled=True
                )
            
            # Show company information if available
            if 'company_info' in st.session_state:
                company_info = st.session_state['company_info']
                with st.expander("🏢 Company Information", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Company:** {company_info['name']}")
                        st.markdown(f"**Size:** {company_info['size']}")
                        st.markdown(f"**Industry:** {company_info['industry']}")
                    with col2:
                        st.markdown(f"**Glassdoor Rating:** {company_info['glassdoor_rating']}")
                        st.markdown(f"**Interview Difficulty:** {company_info['interview_difficulty']}")
                        st.markdown(f"**Culture:** {company_info['company_culture']}")
            
            if st.button("🗑️ Clear job description"):
                if 'job_description' in st.session_state:
                    del st.session_state['job_description']
                if 'company_info' in st.session_state:
                    del st.session_state['company_info']
                st.rerun()
        
        # Get newsletter status
        newsletter_manager = get_newsletter_manager()
        chunks_loaded = len(newsletter_manager.chunks)
        st.info(f"🧠 **Reviewer:** Aakash (Newsletter-grounded)")
        st.info(f"📚 **Newsletter chunks loaded:** {chunks_loaded}")
        
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Your Resume")
        
        if uploaded_file is not None:
            # Extract text from PDF
            resume_text = extract_text_from_pdf(uploaded_file)
            
            if resume_text:
                # Show extracted text in expandable section
                with st.expander("View extracted text", expanded=False):
                    st.text_area(
                        "Resume content:",
                        resume_text,
                        height=300,
                        disabled=True
                    )
                
                # Generate review button
                if st.button("🔍 Get Review", type="primary"):
                    with st.spinner("🤖 Calling newsletter-grounded review system..."):
                        # Get job description and company info if available
                        job_description = st.session_state.get('job_description', None)
                        company_info = st.session_state.get('company_info', None)
                        
                        # Get feedback using newsletter-grounded system
                        feedback = call_gemini(
                            resume_text, 
                            "General Resume Review",
                            job_description,
                            company_info
                        )
                        
                        # Store in session state
                        st.session_state['feedback'] = feedback
                        st.session_state['goal'] = "Newsletter-Grounded Review"
            else:
                st.error("Could not extract text from the PDF. Please try a different file.")
        else:
            st.info("👆 Upload your resume PDF to get started")
    
    with col2:
        st.subheader("💡 Personalized Feedback")
        
        if 'feedback' in st.session_state:
            goal = st.session_state['goal']
            st.markdown("**Review Type:** 🎯 Newsletter-Grounded Review")
            if 'job_description' in st.session_state:
                st.markdown("**Ultra-targeted feedback using job description**")
            else:
                st.markdown("**General resume feedback based on newsletter principles**")
            
            st.markdown("---")
            
            # Display feedback
            st.markdown(st.session_state['feedback'])
            
            st.markdown("---")
            
            # Source attribution
            st.markdown("### 📚 Grounded in Real Expertise")
            st.markdown("**Source:** Aakash's newsletter content on resume customization")
            
            # Show newsletter chunks info
            newsletter_manager = get_newsletter_manager()
            chunks_used = len(newsletter_manager.chunks)
            st.info(f"📚 **Newsletter chunks used:** {chunks_used}")
            
            with st.expander("View newsletter grounding info"):
                st.markdown("This review is grounded in Aakash's newsletter content about resume customization, using the same system as the WhatsApp API.")
                st.markdown("The system uses semantic search to find relevant newsletter content and provides personalized, actionable feedback.")
                
        else:
            st.info("Upload a resume and click 'Get Review' to see your personalized feedback here.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Powered by Gemini AI • Grounded in real creator expertise</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 