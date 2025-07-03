#!/usr/bin/env python3
"""
Test two-way WhatsApp conversation flow with simulated responses.
"""

import requests
import json
from app import app
from flask.testing import FlaskClient

def test_whatsapp_conversation():
    """Test the complete WhatsApp conversation flow."""
    print("🤖 Testing Two-Way WhatsApp Conversation...")
    
    # Test the API endpoint directly
    api_url = "http://localhost:5050/api/whatsapp-upload"
    
    # Test data
    test_data = {
        "resumeUrl": "http://localhost:5050/static/Mandip%20PM%20AI%20Resume%20PD.pdf",
        "jobUrl": "https://job-boards.greenhouse.io/hugeinc/jobs/6978138&gh_src=vhxj4y",
        "phone": "+14379861805",
        "userMessage": "Review my resume!"
    }
    
    print(f"📤 Sending request to: {api_url}")
    print(f"📝 User message: {test_data['userMessage']}")
    
    try:
        response = requests.post(api_url, json=test_data)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('success')}")
            print(f"📊 Newsletter chunks used: {result.get('newsletter_chunks_used')}")
            print(f"🎯 Confidence score: {result.get('confidence_score')}")
            print(f"💬 Message: {result.get('message')}")
            
            # Check WhatsApp result
            whatsapp_result = result.get('whatsapp_result', {})
            if whatsapp_result.get('success'):
                print("✅ WhatsApp messages sent successfully!")
                
                # Check message format
                if 'split_messages' in whatsapp_result:
                    print(f"📱 Split messages sent: {len(whatsapp_result['split_messages'])}")
                elif 'overview_message' in whatsapp_result and 'insights_message' in whatsapp_result:
                    print("📱 Overview + Insights messages sent")
                else:
                    print("📱 Single message sent")
            else:
                print(f"❌ WhatsApp error: {whatsapp_result.get('error')}")
                if "daily messages limit" in str(whatsapp_result.get('error', '')):
                    print("💡 This is expected - Twilio free trial has daily message limits")
                
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_new_conversation_engine():
    """Test the new conversation engine with Flask test client."""
    print("\n🧪 Testing New Conversation Engine Integration...")
    
    with app.test_client() as client:
        # Test 1: Initial message with resume URL
        print("\n📱 Test 1: Initial resume URL")
        twilio_payload = {
            'From': 'whatsapp:+1234567890',
            'To': 'whatsapp:+9876543210',
            'Body': 'http://localhost:5050/static/Mandip%20PM%20AI%20Resume%20PD.pdf',
            'MessageSid': 'SM1234567890abcdef'
        }
        
        response = client.post('/whatsapp-inbound', data=twilio_payload)
        print(f"Status: {response.status_code}")
        response_text = response.data.decode()
        print(f"Response length: {len(response_text)} characters")
        print(f"Response preview: {response_text[:200]}...")
        
        if response.status_code == 200 and "Resume Review by Aakash" in response_text:
            print("✅ Success! Conversation engine started properly")
            
            # Test 2: Follow-up message (user chooses skills)
            print("\n📱 Test 2: User chooses skills (1)")
            twilio_payload = {
                'From': 'whatsapp:+1234567890',
                'To': 'whatsapp:+9876543210',
                'Body': '1',
                'MessageSid': 'SM1234567890abcdef'
            }
            
            response = client.post('/whatsapp-inbound', data=twilio_payload)
            print(f"Status: {response.status_code}")
            response_text = response.data.decode()
            print(f"Response preview: {response_text[:200]}...")
            
            if "Skills & Keywords Analysis" in response_text:
                print("✅ Success! Skills detail message generated")
                
                # Test 3: User asks for examples
                print("\n📱 Test 3: User asks for examples")
                twilio_payload = {
                    'From': 'whatsapp:+1234567890',
                    'To': 'whatsapp:+9876543210',
                    'Body': 'YES',
                    'MessageSid': 'SM1234567890abcdef'
                }
                
                response = client.post('/whatsapp-inbound', data=twilio_payload)
                print(f"Status: {response.status_code}")
                response_text = response.data.decode()
                print(f"Response preview: {response_text[:200]}...")
                
                if "Specific Skills Examples" in response_text:
                    print("✅ Success! Examples provided")
                else:
                    print("❌ Expected examples but got different response")
            else:
                print("❌ Expected skills analysis but got different response")
        else:
            print("❌ Expected resume review but got different response")
            print("This might be due to missing resume file or processing error")

def simulate_whatsapp_conversation():
    """Simulate a complete WhatsApp conversation without sending actual messages."""
    print("\n💬 Simulating Complete WhatsApp Conversation...")
    
    # Simulate the initial review
    print("\n📱 [User] Review my resume!")
    print("🤖 [Bot] ✅ Got your resume! Processing with my newsletter expertise. You'll receive your review soon.")
    print("🤖 [Bot] 📊 Newsletter-grounded review generated successfully!")
    print("🤖 [Bot] 📱 Sending review via WhatsApp...")
    print("🤖 [Bot] 💬 Follow-up questions:")
    print("   🤔 Would you like me to elaborate on any specific point from the review?")
    print("   🎯 Should I help you customize your resume for a different role?")
    print("   📊 Would you like me to analyze a specific section of your resume in more detail?")
    print("   💬 Reply with your choice or ask me anything about the review!")
    
    # Simulate follow-up conversation
    print("\n📱 [User] Can you elaborate on the strengths section?")
    print("🤖 [Bot] 📝 I'd be happy to elaborate! Which specific point from the review would you like me to explain in more detail? You can mention any section or suggestion.")
    
    print("\n📱 [User] Help me customize for a different role")
    print("🤖 [Bot] 🎯 Great! To customize for a different role, please send me the new job posting URL along with your current resume URL.")
    print("🤖 [Bot] Example: https://example.com/resume.pdf https://newjob.company.com/role")
    
    print("\n📱 [User] Show me specific examples")
    print("🤖 [Bot] 💡 I'll provide specific examples! Which suggestion from the review would you like me to show you how to implement?")
    
    print("\n📱 [User] Thanks for the review!")
    print("🤖 [Bot] You're welcome! 🎉 Feel free to reach out anytime for more resume help. Good luck with your job search!")

def test_follow_up_conversation():
    """Test follow-up conversation scenarios."""
    print("\n💬 Testing Follow-up Conversation Scenarios...")
    
    # Simulate different follow-up messages
    follow_up_messages = [
        "Can you elaborate on the strengths section?",
        "Help me customize for a different role",
        "Show me specific examples",
        "Thanks for the review!",
        "Goodbye"
    ]
    
    for message in follow_up_messages:
        print(f"\n📝 Testing: '{message}'")
        
        # Simulate webhook response
        if any(word in message.lower() for word in ['elaborate', 'explain', 'detail', 'more']):
            print("🤖 Response: I'd be happy to elaborate! Which specific point from the review would you like me to explain in more detail?")
        elif any(word in message.lower() for word in ['different', 'role', 'job', 'customize']):
            print("🤖 Response: Great! To customize for a different role, please send me the new job posting URL along with your current resume URL.")
        elif any(word in message.lower() for word in ['example', 'implement', 'how']):
            print("🤖 Response: I'll provide specific examples! Which suggestion from the review would you like me to show you how to implement?")
        elif 'thank' in message.lower():
            print("🤖 Response: You're welcome! Feel free to reach out anytime for more resume help. Good luck with your job search!")
        elif 'bye' in message.lower():
            print("🤖 Response: Goodbye! Feel free to come back anytime for more resume optimization help. Good luck!")
        else:
            print("🤖 Response: I'm here to help with your resume! You can ask me to elaborate, request help with a different role, or ask for specific examples.")

def test_quick_replies():
    """Test quick reply functionality in conversation engine."""
    print("\n🔘 Testing Quick Reply Functionality...")
    
    from core.whatsapp_conversation_engine import start_conversation, continue_conversation
    
    # Mock resume and job data
    resume_data = {
        "success": True,
        "overview": "Strong PM candidate with AI experience",
        "strengths": ["Technical background", "AI/ML experience"],
        "concerns": ["Could improve metrics", "Missing quantifiable results"],
        "suggestions": ["Add metrics", "Quantify achievements"]
    }
    
    job_data = {
        "title": "Product Manager",
        "company": "Tech Company"
    }
    
    # Test 1: Initial conversation with quick replies
    print("\n📱 Test 1: Initial conversation")
    messages, engine_state = start_conversation("User", resume_data, job_data)
    
    quick_replies_found = False
    for msg in messages:
        if 'quick_replies' in msg and msg['quick_replies']:
            quick_replies_found = True
            print(f"✅ Quick replies found: {len(msg['quick_replies'])} options")
            for reply in msg['quick_replies']:
                print(f"   🔘 {reply['title']} (ID: {reply['id']})")
    
    if not quick_replies_found:
        print("❌ No quick replies found in initial conversation")
    
    # Test 2: Follow-up with quick replies
    print("\n📱 Test 2: Follow-up conversation")
    messages, new_engine_state = continue_conversation("1", engine_state)
    
    quick_replies_found = False
    for msg in messages:
        if 'quick_replies' in msg and msg['quick_replies']:
            quick_replies_found = True
            print(f"✅ Quick replies found: {len(msg['quick_replies'])} options")
            for reply in msg['quick_replies']:
                print(f"   🔘 {reply['title']} (ID: {reply['id']})")
    
    if not quick_replies_found:
        print("❌ No quick replies found in follow-up conversation")
    
    # Test 3: Test quick reply integration with Flask
    print("\n📱 Test 3: Flask integration test")
    with app.test_client() as client:
        # Start conversation
        twilio_payload = {
            'From': 'whatsapp:+1234567890',
            'To': 'whatsapp:+9876543210',
            'Body': 'http://localhost:5050/static/Mandip%20PM%20AI%20Resume%20PD.pdf',
            'MessageSid': 'SM1234567890abcdef'
        }
        
        response = client.post('/whatsapp-inbound', data=twilio_payload)
        response_text = response.data.decode()
        
        print(f"📊 Response length: {len(response_text)} characters")
        print(f"📋 Response preview: {response_text[:500]}...")
        
        # Check for quick reply options as plain text
        if 'Reply with one of the following options:' in response_text:
            print("✅ Quick reply options found in TwiML response as plain text")
        else:
            print("❌ Quick reply options NOT found in TwiML response as plain text")
            print("Response preview:", response_text[:500])

if __name__ == "__main__":
    test_whatsapp_conversation()
    test_new_conversation_engine()
    simulate_whatsapp_conversation()
    test_follow_up_conversation()
    test_quick_replies() 