import streamlit as st
import PyPDF2
import io
import os
import requests
import re
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Hardcoded grounding content from Aakash's newsletter
GROUNDING_CONTENT = """The #1 mistake people make in trying to get interviews? Sharing a generic resume or customizing poorly. There are 6 key principles of customization:

1. **Recast our experience to become ideal** - Ask "What archetypes of person would the hiring manager be ecstatic to hire?" Then re-cast as many details as possible to become that person.

2. **Re-tell our story to be a straight line** - Make your winding path seem like a straight line to the job. Remove or minimize jobs that don't fit the archetype.

3. **Customize every bullet for the job** - If bullet points aren't positioning you for the job, the space can be better used. Developer experience might be more exciting than activation lift for internal tools roles.

4. **Use the keywords the ATS seeks** - AI Resume Screening systems look for keyword existence, not meaning. Cover all the bases the job description mentions.

5. **Drop examples to intrigue** - Create a compelling reason to interview you. Drop enough storytelling so they want to follow-up.

6. **Flip your weaknesses** - Identify common reasons you might get disqualified and flip them into strengths through narrative and bullet points."""

# Hardcoded creator
CREATOR = "Aakash"

# Newsletter source link
NEWSLETTER_SOURCE = "https://www.news.aakashg.com/p/how-to-customize-your-resume-to-actually"

# Role-specific context and keywords
ROLE_CONTEXTS = {
    "PM at Series A startup": {
        "archetype": "jack-of-all-trades PM who can wear multiple hats",
        "key_skills": ["resource constraints", "rapid iteration", "cross-functional leadership", "user research", "data analysis", "go-to-market"],
        "metrics_focus": ["user growth", "retention", "conversion", "revenue impact", "time-to-market"],
        "experience_emphasis": ["early-stage", "scrappy", "hands-on", "full-stack PM skills"],
        "keywords": ["MVP", "product-market fit", "user interviews", "analytics", "growth hacking", "lean startup"]
    },
    "Senior PM at Tech Company": {
        "archetype": "experienced PM with proven track record of scaling products",
        "key_skills": ["strategic thinking", "team leadership", "complex product management", "stakeholder management", "data-driven decision making"],
        "metrics_focus": ["business impact", "team productivity", "product quality", "customer satisfaction", "revenue growth"],
        "experience_emphasis": ["scaling", "team management", "strategic planning", "cross-functional collaboration"],
        "keywords": ["strategy", "roadmap", "team leadership", "stakeholder management", "product vision", "execution"]
    },
    "Product Lead at Scale-up": {
        "archetype": "senior PM ready to lead product teams and drive company strategy",
        "key_skills": ["team leadership", "strategic vision", "executive communication", "product strategy", "mentorship"],
        "metrics_focus": ["team performance", "product strategy success", "business outcomes", "team growth", "innovation"],
        "experience_emphasis": ["leading teams", "strategic initiatives", "executive presentations", "mentoring"],
        "keywords": ["product strategy", "team leadership", "executive communication", "mentorship", "strategic planning"]
    },
    "Head of Product": {
        "archetype": "executive-level product leader who can drive company-wide product strategy",
        "key_skills": ["executive leadership", "company strategy", "team building", "board communication", "product vision"],
        "metrics_focus": ["company growth", "product portfolio success", "team scaling", "market position", "revenue impact"],
        "experience_emphasis": ["executive leadership", "company strategy", "team building", "board-level work"],
        "keywords": ["executive leadership", "product strategy", "team building", "board communication", "company vision"]
    },
    "PM at FAANG": {
        "archetype": "high-performing PM with strong technical and analytical skills",
        "key_skills": ["technical depth", "data analysis", "A/B testing", "algorithmic thinking", "large-scale systems"],
        "metrics_focus": ["user engagement", "performance metrics", "algorithm efficiency", "scale", "data quality"],
        "experience_emphasis": ["technical products", "data-driven decisions", "large-scale impact", "algorithmic thinking"],
        "keywords": ["A/B testing", "data analysis", "algorithms", "large-scale", "technical depth", "metrics"]
    },
    "Technical PM": {
        "archetype": "PM with strong technical background who can bridge product and engineering",
        "key_skills": ["technical architecture", "engineering collaboration", "system design", "technical strategy", "API design"],
        "metrics_focus": ["system performance", "technical debt", "development velocity", "code quality", "architecture efficiency"],
        "experience_emphasis": ["technical products", "engineering collaboration", "system design", "technical strategy"],
        "keywords": ["technical architecture", "system design", "API", "engineering", "technical strategy", "development"]
    },
    "Growth PM": {
        "archetype": "PM focused on user acquisition, retention, and business growth",
        "key_skills": ["growth hacking", "user acquisition", "retention strategies", "analytics", "experimentation"],
        "metrics_focus": ["user growth", "retention rates", "acquisition costs", "conversion rates", "viral coefficients"],
        "experience_emphasis": ["growth experiments", "user acquisition", "retention optimization", "analytics"],
        "keywords": ["growth hacking", "user acquisition", "retention", "experimentation", "analytics", "conversion"]
    },
    "Platform PM": {
        "archetype": "PM who builds products that enable other products and teams",
        "key_skills": ["platform thinking", "API design", "developer experience", "ecosystem building", "technical strategy"],
        "metrics_focus": ["developer adoption", "platform usage", "API performance", "ecosystem growth", "developer satisfaction"],
        "experience_emphasis": ["platform products", "developer experience", "API design", "ecosystem building"],
        "keywords": ["platform", "API", "developer experience", "ecosystem", "technical strategy", "developer tools"]
    }
}

def get_role_context(role: str) -> dict:
    """Get role-specific context for the given role."""
    return ROLE_CONTEXTS.get(role, ROLE_CONTEXTS["PM at Series A startup"])

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

def call_gemini(prompt: str, goal: str = "PM at Series A startup") -> str:
    """
    Call the real Gemini API with the provided prompt.
    """
    try:
        # Initialize the model
        model = genai.GenerativeModel('gemma-3n-e4b-it')
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Return the response text
        return response.text
        
    except Exception as e:
        st.error(f"Error calling Gemini API: {str(e)}")
        # Fallback to mock response if API fails
        role_context = get_role_context(goal)
        
        return f"""Here are 3-5 specific improvements for your resume based on the 6 key principles of customization for {goal}:

**1. Recast your experience to become the ideal {goal} candidate**
📌 **Principle 1: "Ask 'What archetypes of person would the hiring manager be ecstatic to hire?' Then re-cast as many details as possible to become that person."**

For {goal}, you need to become a {role_context['archetype']}. Emphasize: {', '.join(role_context['key_skills'][:3])}. Replace generic PM bullets with these specific skills.

**2. Create a straight-line narrative to {goal}**
📌 **Principle 2: "Make your winding path seem like a straight line to the job."**

Focus on experiences that demonstrate: {', '.join(role_context['experience_emphasis'][:3])}. Minimize or remove experiences that don't align with this archetype.

**3. Customize every bullet point for {goal}**
📌 **Principle 3: "If bullet points aren't positioning you for the job, the space can be better used."**

Emphasize metrics like: {', '.join(role_context['metrics_focus'][:3])}. These are what {goal} hiring managers care about most.

**4. Optimize for ATS with {goal} keywords**
📌 **Principle 4: "AI Resume Screening systems look for keyword existence, not meaning."**

Incorporate these keywords naturally: {', '.join(role_context['keywords'][:4])}. These will help you pass ATS screening for {goal} roles.

**5. Add intrigue through {goal}-specific storytelling**
📌 **Principle 5: "Create a compelling reason to interview you."**

Include examples that demonstrate your {role_context['archetype']} capabilities and make {goal} recruiters want to learn more.

Each improvement should help you move from a generic resume to one that's specifically tailored for {goal} opportunities."""

def extract_text_from_pdf(pdf_file) -> Optional[str]:
    """Extract text content from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def create_review_prompt(resume_text: str, goal: str, creator: str, grounding_content: str, job_description: str = None, company_info: dict = None) -> str:
    """Create the structured prompt for Gemini."""
    
    # Base prompt
    if goal:
        # Get role-specific context
        role_context = get_role_context(goal)
        
        prompt = f"""You are {creator}. A reader submitted the following resume excerpt and asked for feedback on how to improve it for the goal: {goal}.

**ROLE-SPECIFIC CONTEXT:**
- Target Archetype: {role_context['archetype']}
- Key Skills to Emphasize: {', '.join(role_context['key_skills'])}
- Metrics Focus: {', '.join(role_context['metrics_focus'])}
- Experience to Highlight: {', '.join(role_context['experience_emphasis'])}
- Keywords for ATS: {', '.join(role_context['keywords'])}

Please analyze their resume using the 6 key principles of customization from my article:

{grounding_content}

Provide feedback that:
- Addresses 3-5 specific areas for improvement based on these principles
- Focuses on how to customize their resume for the target role: {goal}
- Uses the role-specific context above to provide targeted advice
- Uses specific examples from their resume to illustrate your points
- Grounds suggestions in the principles above
- Uses your authentic tone and voice
- Includes relevant quotes or paraphrases from the article
- Provides actionable, specific advice (not generic tips)
- Incorporates the keywords and skills relevant to {goal}"""

    else:
        # Job description only (no specific role type)
        prompt = f"""You are {creator}. A reader submitted the following resume excerpt and asked for feedback on how to improve it for a specific job posting.

Please analyze their resume using the 6 key principles of customization from my article:

{grounding_content}

Provide feedback that:
- Addresses 3-5 specific areas for improvement based on these principles
- Uses specific examples from their resume to illustrate your points
- Grounds suggestions in the principles above
- Uses your authentic tone and voice
- Includes relevant quotes or paraphrases from the article
- Provides actionable, specific advice (not generic tips)"""

    # Add job description context if provided
    if job_description:
        prompt += f"""

**JOB DESCRIPTION CONTEXT:**
The user provided a specific job description. Use this to make your feedback ultra-targeted:

{job_description}"""

        # Add company information if available
        if company_info:
            prompt += f"""

**COMPANY CONTEXT:**
Company: {company_info['name']}
Size: {company_info['size']}
Industry: {company_info['industry']}
Glassdoor Rating: {company_info['glassdoor_rating']}
Interview Difficulty: {company_info['interview_difficulty']}
Company Culture: {company_info['company_culture']}

Use this company information to:
- Tailor your advice to the company's size and stage
- Consider the company culture and values
- Factor in the interview difficulty level
- Align with the industry-specific requirements"""

        prompt += f"""

Additional requirements:
- Extract key requirements, skills, and keywords from the job description
- Suggest how to align their resume with the specific company and role
- Identify any gaps between their experience and the job requirements
- Recommend how to address those gaps in their resume
- Use the exact terminology and keywords from the job posting
- Consider the company's size, culture, and interview process"""

    prompt += f"""

Resume:
{resume_text}"""
    
    return prompt

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
        
        # Choose between role type or job URL
        st.subheader("🎯 Choose Your Target")
        
        target_option = st.radio(
            "How would you like to target your resume?",
            ["Role Type", "Specific Job Posting"],
            help="Choose between general role-based feedback or specific job posting feedback"
        )
        
        selected_goal = None
        job_description_text = None
        
        if target_option == "Role Type":
            # Review goal dropdown
            review_goals = [
                "PM at Series A startup",
                "Senior PM at Tech Company",
                "Product Lead at Scale-up",
                "Head of Product",
                "PM at FAANG",
                "Technical PM",
                "Growth PM",
                "Platform PM"
            ]
            
            selected_goal = st.selectbox(
                "Select your target role:",
                review_goals,
                help="Choose the type of role you're targeting for tailored feedback"
            )
            
        else:  # Specific Job Posting
            job_url = st.text_input(
                "Job posting URL:",
                placeholder="https://jobs.company.com/product-manager",
                help="Paste the URL of a specific job posting for ultra-targeted feedback"
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
        
        st.info(f"🧠 **Reviewer:** {CREATOR}")
        
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
                    with st.spinner("🤖 Calling Gemini AI for personalized review..."):
                        # Get job description and company info if available
                        job_description = st.session_state.get('job_description', None)
                        company_info = st.session_state.get('company_info', None)
                        
                        # Create prompt
                        prompt = create_review_prompt(
                            resume_text, 
                            selected_goal, 
                            CREATOR, 
                            GROUNDING_CONTENT,
                            job_description,
                            company_info
                        )
                        
                        # Get feedback from Gemini
                        feedback = call_gemini(prompt, selected_goal or "Specific Job Posting")
                        
                        # Store in session state
                        st.session_state['feedback'] = feedback
                        st.session_state['goal'] = selected_goal or "Specific Job Posting"
            else:
                st.error("Could not extract text from the PDF. Please try a different file.")
        else:
            st.info("👆 Upload your resume PDF to get started")
    
    with col2:
        st.subheader("💡 Personalized Feedback")
        
        if 'feedback' in st.session_state:
            goal = st.session_state['goal']
            if goal == "Specific Job Posting":
                st.markdown("**Target:** 🎯 Specific Job Posting")
                if 'job_description' in st.session_state:
                    st.markdown("**Ultra-targeted feedback using job description**")
            else:
                st.markdown(f"**Target Role:** {goal}")
            
            st.markdown("---")
            
            # Display feedback
            st.markdown(st.session_state['feedback'])
            
            st.markdown("---")
            
            # Source attribution
            st.markdown("### 📚 Grounded in Real Expertise")
            st.markdown(f"**Source Article:** [How to customize your resume to actually get PM interviews]({NEWSLETTER_SOURCE})")
            
            with st.expander("View the 6 key principles"):
                st.markdown(f'> "{GROUNDING_CONTENT}"')
                st.markdown(f"— {CREATOR}")
                
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