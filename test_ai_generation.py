#!/usr/bin/env python3
"""
Test to see what the AI is actually generating and debug the short response issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.whatsapp_prompt import NewsletterGroundedReviewer
from core.newsletter_manager import NewsletterManager

def test_ai_generation_detailed():
    """Test AI generation with detailed logging."""
    print("=== Testing AI Generation in Detail ===")
    
    reviewer = NewsletterGroundedReviewer()
    
    # Test with sample resume text
    sample_resume = """
    JOHN DOE
    Software Engineer
    
    EXPERIENCE
    Senior Software Engineer | Tech Company | 2020-2023
    • Developed and maintained web applications using React and Node.js
    • Led a team of 3 developers to deliver features on time
    • Improved application performance by 40% through optimization
    
    Software Engineer | Startup | 2018-2020
    • Built REST APIs using Python and Django
    • Collaborated with product team to define requirements
    • Implemented automated testing reducing bugs by 30%
    
    SKILLS
    JavaScript, Python, React, Node.js, Django, Git, AWS
    """
    
    # Test with job URL
    job_url = "https://job-boards.greenhouse.io/hugeinc/jobs/6978138&gh_src=vhxj4y"
    
    print("Step 1: Parse job description...")
    jd_parsed = reviewer.jd_parser.parse_job_url(job_url)
    print(f"JD parsing success: {jd_parsed.get('success', False)}")
    
    if jd_parsed.get('success'):
        jd_keywords = reviewer.jd_parser.extract_keywords_for_matching(jd_parsed)
        print(f"Extracted {len(jd_keywords)} keywords: {jd_keywords[:10]}...")
    else:
        jd_keywords = []
        print("Using general keywords")
        jd_keywords = ['resume', 'customization', 'interview', 'experience', 'skills']
    
    print("\nStep 2: Get newsletter content...")
    relevant_chunks = reviewer.newsletter_manager.get_relevant_content(jd_keywords, max_chunks=5)
    print(f"Found {len(relevant_chunks)} relevant chunks")
    
    for i, chunk in enumerate(relevant_chunks):
        print(f"Chunk {i+1}: {chunk.section}")
        print(f"Content preview: {chunk.content[:100]}...")
    
    print("\nStep 3: Calculate confidence score...")
    scoring_result = reviewer.relevance_scorer.calculate_confidence_score(
        sample_resume, jd_keywords, relevant_chunks
    )
    print(f"Confidence score: {scoring_result['confidence_score']}")
    
    print("\nStep 4: Prepare newsletter content for prompt...")
    newsletter_content = reviewer._prepare_newsletter_content_for_prompt(relevant_chunks)
    print(f"Newsletter content length: {len(newsletter_content)} characters")
    print("Newsletter content preview:")
    print(newsletter_content[:500] + "..." if len(newsletter_content) > 500 else newsletter_content)
    
    print("\nStep 5: Create prompts...")
    system_prompt = reviewer._create_system_prompt()
    user_prompt = reviewer._create_user_prompt(
        sample_resume, jd_parsed, newsletter_content, scoring_result
    )
    
    print(f"System prompt length: {len(system_prompt)}")
    print(f"User prompt length: {len(user_prompt)}")
    
    print("\nSystem prompt:")
    print(system_prompt)
    
    print("\nUser prompt preview:")
    print(user_prompt[:1000] + "..." if len(user_prompt) > 1000 else user_prompt)
    
    print("\nStep 6: Generate AI response...")
    try:
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        print(f"Full prompt length: {len(full_prompt)}")
        
        response = reviewer.gemini_model.generate_content(full_prompt)
        print(f"✅ Gemini API call successful")
        print(f"Response length: {len(response.text)} characters")
        print(f"Response text:")
        print(response.text)
        
        # Check if response contains actual review content
        if "Overall Assessment" in response.text or "Strengths" in response.text or "Areas to Improve" in response.text:
            print("✅ Response contains review content")
        else:
            print("❌ Response does not contain expected review content")
            
    except Exception as e:
        print(f"❌ Gemini API call failed: {e}")
        return None
    
    return response.text

def test_with_simplified_prompt():
    """Test with a simplified prompt to see if the issue is prompt complexity."""
    print("\n=== Testing with Simplified Prompt ===")
    
    reviewer = NewsletterGroundedReviewer()
    
    # Simple test resume
    sample_resume = """
    JOHN DOE
    Software Engineer
    
    EXPERIENCE
    Senior Software Engineer | Tech Company | 2020-2023
    • Developed web applications using React and Node.js
    • Led a team of 3 developers
    • Improved performance by 40%
    
    SKILLS
    JavaScript, Python, React, Node.js
    """
    
    # Simplified prompt
    simple_prompt = """You are Aakash, a resume expert. Based on the newsletter content below, provide a resume review.

Newsletter Content:
## 1. Recast Your Experience to Become Ideal
Ask "What archetypes of person would the hiring manager be ecstatic to hire?" Then re-cast as many details as possible to become that person.

## 2. Customize Every Bullet for the Job
If bullet points aren't positioning you for the job, the space can be better used.

Resume:
{sample_resume}

Please provide a resume review with:
1. Overall Assessment
2. Strengths
3. Areas to Improve
4. Next Steps

Keep it under 1000 characters.""".format(sample_resume=sample_resume)
    
    print("Testing with simplified prompt...")
    try:
        response = reviewer.gemini_model.generate_content(simple_prompt)
        print(f"Response length: {len(response.text)} characters")
        print(f"Response:")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 AI Generation Debug Test")
    print("=" * 50)
    
    # Run detailed test
    response = test_ai_generation_detailed()
    
    # Run simplified test
    test_with_simplified_prompt()
    
    print("\n" + "=" * 50)
    print("📊 ANALYSIS")
    if response:
        if len(response) < 200:
            print("❌ ISSUE: AI generating very short responses")
        elif "Overall Assessment" not in response and "Strengths" not in response:
            print("❌ ISSUE: AI not following prompt structure")
        else:
            print("✅ AI generation appears to be working")
    else:
        print("❌ ISSUE: AI generation failed") 