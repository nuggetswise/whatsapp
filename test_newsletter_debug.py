#!/usr/bin/env python3
"""
Debug script to test newsletter content retrieval and identify issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.newsletter_manager import NewsletterManager
from core.jd_parser import JobDescriptionParser
from core.whatsapp_prompt import NewsletterGroundedReviewer

def test_newsletter_manager():
    """Test newsletter manager directly."""
    print("=== Testing Newsletter Manager ===")
    
    nm = NewsletterManager()
    print(f"Loaded {len(nm.chunks)} newsletter chunks")
    
    # Test with general keywords
    general_keywords = ['resume', 'customization', 'interview', 'experience', 'skills']
    relevant_chunks = nm.get_relevant_content(general_keywords, max_chunks=5)
    print(f"Found {len(relevant_chunks)} relevant chunks for general keywords")
    
    for i, chunk in enumerate(relevant_chunks):
        print(f"Chunk {i+1}: {chunk.section} (topics: {chunk.topics})")
    
    return relevant_chunks

def test_jd_parser():
    """Test job description parser."""
    print("\n=== Testing JD Parser ===")
    
    jd_parser = JobDescriptionParser()
    
    # Test with the actual job URL from the issue
    job_url = "https://job-boards.greenhouse.io/hugeinc/jobs/6978138&gh_src=vhxj4y"
    print(f"Testing with job URL: {job_url}")
    
    jd_parsed = jd_parser.parse_job_url(job_url)
    print(f"JD parsing success: {jd_parsed.get('success', False)}")
    
    if jd_parsed.get('success'):
        jd_keywords = jd_parser.extract_keywords_for_matching(jd_parsed)
        print(f"Extracted {len(jd_keywords)} keywords: {jd_keywords[:10]}...")
        return jd_keywords
    else:
        print(f"JD parsing failed: {jd_parsed.get('error', 'Unknown error')}")
        return []

def test_newsletter_reviewer():
    """Test the newsletter reviewer directly."""
    print("\n=== Testing Newsletter Reviewer ===")
    
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
    
    print("Processing resume review...")
    result = reviewer.process_resume_review(sample_resume, job_url)
    
    print(f"Review success: {result['success']}")
    print(f"Newsletter chunks used: {result['newsletter_chunks_used']}")
    print(f"Confidence score: {result['confidence_score']}")
    
    if result['success']:
        print(f"Review length: {len(result['review'])} characters")
        print("\nReview preview:")
        print(result['review'][:500] + "..." if len(result['review']) > 500 else result['review'])
    
    return result

def test_content_generation_length():
    """Test content generation length to see if truncation is happening."""
    print("\n=== Testing Content Generation Length ===")
    
    reviewer = NewsletterGroundedReviewer()
    
    # Test with a longer resume to see if we hit character limits
    long_resume = """
    JANE SMITH
    Product Manager
    
    EXPERIENCE
    Senior Product Manager | Big Tech | 2021-2023
    • Led product strategy for a $50M revenue product line
    • Managed cross-functional team of 15 engineers, designers, and analysts
    • Increased user engagement by 60% through data-driven feature development
    • Launched 3 major product features that drove 25% revenue growth
    • Collaborated with engineering to improve development velocity by 40%
    • Conducted user research with 200+ customers to inform product decisions
    • Worked with marketing to develop go-to-market strategies for new features
    • Analyzed competitive landscape and market trends to inform roadmap
    • Mentored 3 junior product managers and established best practices
    • Presented product strategy to executive leadership and board members
    
    Product Manager | Startup | 2019-2021
    • Built and launched MVP for B2B SaaS product from concept to market
    • Grew user base from 0 to 10,000 active users in 18 months
    • Defined product requirements and user stories for development team
    • Conducted customer interviews and usability testing sessions
    • Worked with sales team to develop pricing strategy and sales materials
    • Analyzed user behavior data to optimize product features
    • Coordinated with engineering team to prioritize and deliver features
    • Created product documentation and training materials for customers
    • Managed relationships with key enterprise customers and partners
    • Developed and executed customer success and retention strategies
    
    Associate Product Manager | Tech Company | 2017-2019
    • Supported senior product managers in feature development and analysis
    • Conducted market research and competitive analysis for new products
    • Created product specifications and requirements documents
    • Worked with design team to create user interface mockups
    • Coordinated with engineering team to track development progress
    • Analyzed product metrics and user feedback to inform decisions
    • Assisted in A/B testing and experimentation for feature optimization
    • Created product training materials and documentation
    • Supported customer support team with product-related inquiries
    • Participated in agile development processes and sprint planning
    
    SKILLS
    Product Strategy, User Research, Data Analysis, A/B Testing, Agile Development,
    User Experience Design, Market Research, Competitive Analysis, Go-to-Market Strategy,
    Customer Success, Stakeholder Management, Cross-functional Leadership, SQL, Python,
    Tableau, Figma, Jira, Confluence, Salesforce, HubSpot
    """
    
    job_url = "https://job-boards.greenhouse.io/hugeinc/jobs/6978138&gh_src=vhxj4y"
    
    print("Processing long resume review...")
    result = reviewer.process_resume_review(long_resume, job_url)
    
    print(f"Review success: {result['success']}")
    print(f"Newsletter chunks used: {result['newsletter_chunks_used']}")
    print(f"Review length: {len(result['review'])} characters")
    print(f"Max allowed: {reviewer.MAX_OUTPUT_CHAR if hasattr(reviewer, 'MAX_OUTPUT_CHAR') else 'Unknown'}")
    
    if len(result['review']) > 1500:
        print("⚠️  Review exceeds character limit - truncation may have occurred")
    else:
        print("✅ Review within character limits")
    
    return result

if __name__ == "__main__":
    print("🔍 Newsletter Content Debug Test")
    print("=" * 50)
    
    # Run all tests
    chunks = test_newsletter_manager()
    keywords = test_jd_parser()
    result = test_newsletter_reviewer()
    long_result = test_content_generation_length()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"Newsletter chunks loaded: {len(chunks)}")
    print(f"JD keywords extracted: {len(keywords)}")
    print(f"Review newsletter chunks used: {result['newsletter_chunks_used']}")
    print(f"Long review newsletter chunks used: {long_result['newsletter_chunks_used']}")
    
    if result['newsletter_chunks_used'] == 0:
        print("❌ ISSUE FOUND: Newsletter chunks not being used in review!")
    else:
        print("✅ Newsletter chunks are being used correctly") 