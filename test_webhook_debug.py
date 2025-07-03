#!/usr/bin/env python3
"""
Test webhook PDF extraction logic exactly as it happens in the webhook.
"""

import requests
import io
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.creator_review import extract_text_from_pdf

def test_webhook_pdf_extraction():
    """Test PDF extraction exactly as the webhook does it."""
    print("🔍 Testing Webhook PDF Extraction Logic...")
    
    # Test the static PDF URL (same as webhook)
    pdf_url = "http://localhost:5050/static/Mandip%20PM%20AI%20Resume%20PD.pdf"
    
    try:
        print(f"📥 Downloading PDF from: {pdf_url}")
        resume_response = requests.get(pdf_url)
        
        print(f"📊 Resume download status: {resume_response.status_code}")
        print(f"📊 Resume content length: {len(resume_response.content)} bytes")
        
        if resume_response.status_code == 200:
            # Test PDF extraction (exactly as webhook does it)
            print("🔍 Extracting text from PDF...")
            resume_content = resume_response.content
            resume_text = extract_text_from_pdf(io.BytesIO(resume_content))
            
            print(f"📊 Extracted text length: {len(resume_text) if resume_text else 0} characters")
            
            if not resume_text:
                print("❌ Text extraction failed - returned None")
                return False
            
            # Check if text is meaningful (same logic as webhook)
            if len(resume_text.strip()) < 100:
                print("❌ Text too short - less than 100 characters")
                print(f"📝 Text content: {resume_text[:200]}...")
                return False
            
            print("✅ Text extraction successful and meaningful!")
            print(f"📝 Text preview: {resume_text[:200]}...")
            return True
                
        else:
            print(f"❌ Failed to download PDF: {resume_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_webhook_pdf_extraction()
    if success:
        print("\n✅ Webhook PDF extraction should work!")
    else:
        print("\n❌ Webhook PDF extraction will fail!") 