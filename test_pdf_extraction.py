#!/usr/bin/env python3
"""
Test PDF extraction to debug webhook issues.
"""

import requests
import io
from core.creator_review import extract_text_from_pdf

def test_pdf_extraction():
    """Test PDF extraction from the static URL."""
    print("🔍 Testing PDF Extraction...")
    
    # Test the static PDF URL
    pdf_url = "http://localhost:5050/static/Mandip%20PM%20AI%20Resume%20PD.pdf"
    
    try:
        print(f"📥 Downloading PDF from: {pdf_url}")
        response = requests.get(pdf_url)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Content type: {response.headers.get('content-type')}")
        print(f"📊 Content length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Test PDF extraction
            print("🔍 Extracting text from PDF...")
            pdf_content = io.BytesIO(response.content)
            extracted_text = extract_text_from_pdf(pdf_content)
            
            if extracted_text:
                print(f"✅ Text extraction successful!")
                print(f"📊 Extracted text length: {len(extracted_text)} characters")
                print(f"📝 Text preview: {extracted_text[:200]}...")
                
                # Check if text is meaningful
                if len(extracted_text.strip()) < 50:
                    print("⚠️  Warning: Extracted text seems too short")
                else:
                    print("✅ Text appears to be meaningful")
                    
            else:
                print("❌ Text extraction failed - returned None")
                
        else:
            print(f"❌ Failed to download PDF: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pdf_extraction() 