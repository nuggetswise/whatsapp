#!/usr/bin/env python3
"""
Test the updated prompts with company-specific Next Steps.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.whatsapp_prompt import NewsletterGroundedReviewer
from core.creator_review import extract_text_from_pdf

def test_updated_prompts():
    """Test the updated prompts with real data."""
    print("🧪 Testing Updated Prompts with Company-Specific Next Steps...")
    
    # Initialize reviewer
    reviewer = NewsletterGroundedReviewer()
    
    # Extract real resume text
    print("📄 Extracting real resume text...")
    resume_text = extract_text_from_pdf('static/Mandip PM AI Resume PD.pdf')
    if not resume_text:
        print("❌ Failed to extract resume text")
        return False
    
    print(f"✅ Extracted {len(resume_text)} characters from resume")
    
    # Real job URL with company name
    job_url = "https://job-boards.greenhouse.io/hugeinc/jobs/6978138&gh_src=vhxj4y"
    print(f"🎯 Testing with job URL: {job_url}")
    
    # Process review with real data
    print("🤖 Calling Gemini API with updated prompts...")
    result = reviewer.process_resume_review(resume_text, job_url)
    
    if not result['success']:
        print(f"❌ Review failed: {result.get('error')}")
        return False
    
    # Check the review content
    review_text = result['review']
    character_count = len(review_text)
    
    print(f"\n📊 Results:")
    print(f"Character count: {character_count}")
    print(f"Confidence score: {result.get('confidence_score', 0)}")
    print(f"JD overlap: {result.get('scoring_details', {}).get('jd_resume_overlap', 0)}%")
    print(f"Newsletter chunks used: {result.get('newsletter_chunks_used', 0)}")
    
    # Check for company-specific Next Steps
    company_specific_indicators = [
        "Next Steps for HugeInc",
        "Next Steps for the target company",
        "Research HugeInc",
        "Research the target company"
    ]
    
    has_company_specific = any(indicator in review_text for indicator in company_specific_indicators)
    
    if has_company_specific:
        print("✅ Company-specific Next Steps found")
    else:
        print("❌ Company-specific Next Steps missing")
    
    # Check for required elements
    required_elements = [
        "🎯 *Resume Review by Aakash*",
        "💪 *Key Strengths:*",
        "🔧 *Areas to Improve:*",
        "🎯 *Next Steps for",
        "📚 *Based on my newsletter:",
        "🔗 https://www.news.aakashg.com"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in review_text:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing required elements: {missing_elements}")
        return False
    
    print("✅ All required elements present")
    
    # Check character limit
    max_char = int(os.getenv('MAX_OUTPUT_CHAR', 1500))
    if character_count > max_char:
        print(f"❌ Message too long: {character_count} characters (limit: {max_char})")
        return False
    
    print(f"✅ Message length OK: {character_count} characters")
    
    # Show the Next Steps section specifically
    print(f"\n🎯 Next Steps Section:")
    lines = review_text.split('\n')
    next_steps_started = False
    for line in lines:
        if "🎯 *Next Steps for" in line:
            next_steps_started = True
            print(line)
        elif next_steps_started and line.strip().startswith('📚'):
            print(line)
            break
        elif next_steps_started and line.strip():
            print(line)
    
    return True

if __name__ == "__main__":
    success = test_updated_prompts()
    if success:
        print("\n🎉 Updated prompts test passed!")
    else:
        print("\n❌ Updated prompts test failed!")
        sys.exit(1) 