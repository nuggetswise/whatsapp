#!/usr/bin/env python3
"""
Test to debug the formatting and truncation issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.whatsapp_prompt import NewsletterGroundedReviewer

def test_formatting_issue():
    """Test the formatting issue step by step."""
    print("=== Testing Formatting Issue ===")
    
    reviewer = NewsletterGroundedReviewer()
    
    # This is the actual AI response from our test
    ai_response = """Hey John,

1. **Overall Assessment:** Your resume needs some work to really shine for the Director, Product Management role at HugeInc.  It's currently not showcasing you as the ideal candidate.

2. **Strengths:** You've included relevant technical skills like Python and JavaScript, which is good.

3. **Areas to Improve:**  Based on my newsletter principles, your bullet points aren't customized for this specific role.  The hiring manager at HugeInc wants to see how your experience translates to their needs, particularly in UI and AI. As I mention in my content,  recasting your experience to match the "ideal" candidate is crucial.  Currently, your descriptions are generic and don't highlight achievements relevant to product management in UI and AI.

4. **Next Steps for HugeInc Role:**
    * **Recast your experience:**  Think "What would make a HugeInc hiring manager ecstatic?"  Then, rewrite your bullet points to reflect that.  For example, quantify the impact of your projects on user experience (UI) if possible.  Showcase any experience with AI development or implementation.
    * **Customize bullet points:**  Focus on the impact your work had. Instead of simply listing tasks, highlight the results.  If a bullet point doesn't position you for this specific role at HugeInc (consider UI/AI focus), remove or rewrite it.
    *  **Add keywords:** Strategically add keywords related to UI and AI development (I haven't covered keyword optimization beyond this in my content yet)  to your experience section and skills section."""
    
    print(f"Original AI response length: {len(ai_response)} characters")
    print("Original AI response:")
    print(ai_response)
    print("\n" + "="*50)
    
    # Step 1: Clean the review text
    cleaned_text = reviewer._clean_review_text(ai_response)
    print(f"Cleaned text length: {len(cleaned_text)} characters")
    print("Cleaned text:")
    print(cleaned_text)
    print("\n" + "="*50)
    
    # Step 2: Format for WhatsApp
    scoring_result = {'confidence_score': 26}
    whatsapp_text = reviewer._format_for_whatsapp(ai_response, scoring_result)
    print(f"WhatsApp formatted text length: {len(whatsapp_text)} characters")
    print("WhatsApp formatted text:")
    print(whatsapp_text)
    print("\n" + "="*50)
    
    # Step 3: Check if truncation would happen
    max_char = 1500
    if len(whatsapp_text) > max_char:
        print(f"⚠️  Text exceeds {max_char} characters - truncation would occur")
        truncated_text = reviewer._truncate_for_whatsapp(whatsapp_text, max_char)
        print(f"Truncated text length: {len(truncated_text)} characters")
        print("Truncated text:")
        print(truncated_text)
    else:
        print(f"✅ Text within {max_char} character limit")
    
    # Step 4: Test the truncation logic
    print("\n" + "="*50)
    print("Testing truncation logic...")
    
    # Create a longer version to force truncation
    long_whatsapp_text = whatsapp_text + "\n\n" + "Additional content " * 50
    print(f"Long text length: {len(long_whatsapp_text)} characters")
    
    truncated = reviewer._truncate_for_whatsapp(long_whatsapp_text, max_char)
    print(f"Truncated length: {len(truncated)} characters")
    print("Truncated result:")
    print(truncated)

def test_section_detection():
    """Test how the truncation logic detects sections."""
    print("\n=== Testing Section Detection ===")
    
    # Test different section formats
    test_texts = [
        "1. **Overall Assessment:** Content here",
        "1. *Overall Assessment:* Content here", 
        "💪 *Key Strengths:* Content here",
        "🔧 *Areas to Improve:* Content here",
        "🎯 *Next Steps:* Content here"
    ]
    
    for text in test_texts:
        print(f"Testing: {text}")
        # Check if it would be detected as a section header
        keywords = ["💪 *Key Strengths:*", "🔧 *Areas to Improve:*", "🎯 *Next Steps", "📚 *Based on my newsletter"]
        is_section = any(keyword in text for keyword in keywords)
        print(f"  Detected as section: {is_section}")

if __name__ == "__main__":
    print("🔍 Formatting Debug Test")
    print("=" * 50)
    
    test_formatting_issue()
    test_section_detection()
    
    print("\n" + "=" * 50)
    print("📊 ANALYSIS")
    print("The issue is likely in the section detection logic during truncation.") 