#!/usr/bin/env python3
"""
Demonstration of the newsletter-grounded resume review system.
Shows how the system generates authentic, newsletter-based feedback.
"""

from core.whatsapp_prompt import NewsletterGroundedReviewer
from core.newsletter_manager import NewsletterManager
from core.relevance_scorer import RelevanceScorer

def demo_newsletter_grounded_review():
    """Demonstrate the newsletter-grounded review system."""
    print("🎯 Newsletter-Grounded Resume Review System Demo\n")
    
    # Initialize the system
    reviewer = NewsletterGroundedReviewer()
    
    # Sample resume text
    resume_text = """
    Sarah Johnson
    Product Manager
    
    EXPERIENCE
    
    Senior Product Manager | TechCorp Inc. | 2022-Present
    • Led cross-functional team of 8 engineers and designers
    • Increased user engagement by 35% through data-driven optimization
    • Managed $2M product budget and stakeholder communications
    • Conducted user research with 500+ participants
    
    Product Manager | StartupXYZ | 2020-2022
    • Built MVP from concept to 10K users in 6 months
    • Implemented agile methodologies and sprint planning
    • Collaborated with engineering team on technical requirements
    
    SKILLS
    Product Strategy, Data Analysis, User Research, Agile, A/B Testing, 
    Stakeholder Management, Technical Writing, SQL, Python
    """
    
    print("📄 Sample Resume:")
    print("=" * 50)
    print(resume_text)
    print("=" * 50)
    
    # Generate newsletter-grounded review
    print("\n🔍 Generating Newsletter-Grounded Review...")
    result = reviewer.process_resume_review(resume_text)
    
    if result['success']:
        print("\n✅ Review Generated Successfully!")
        print(f"📊 Confidence Score: {result['confidence_score']}/100")
        print(f"📰 Newsletter Chunks Used: {result['newsletter_chunks_used']}")
        print(f"📏 Review Length: {len(result['review'])} characters")
        
        print("\n📱 Newsletter-Grounded Feedback:")
        print("=" * 50)
        print(result['review'])
        print("=" * 50)
        
        # Show newsletter content that was used
        print("\n📰 Newsletter Content Referenced:")
        print("=" * 50)
        nm = NewsletterManager()
        chunks = nm.get_relevant_content(['resume', 'customization'], max_chunks=1)
        if chunks:
            print(f"Article: {chunks[0].article_name}")
            print(f"Section: {chunks[0].section}")
            print(f"Topics: {', '.join(chunks[0].topics[:5])}...")
        print("=" * 50)
        
    else:
        print(f"❌ Review generation failed: {result.get('error')}")

def demo_relevance_scoring():
    """Demonstrate the relevance scoring system."""
    print("\n🎯 Relevance Scoring Demo\n")
    
    nm = NewsletterManager()
    scorer = RelevanceScorer(nm)
    
    # Test with different scenarios
    scenarios = [
        {
            "name": "Product Manager Resume",
            "resume": "Product Manager with 5 years experience in data analysis and user research",
            "jd_keywords": ["product management", "data analysis", "user research", "agile"]
        },
        {
            "name": "Software Engineer Resume", 
            "resume": "Software Engineer with Python, JavaScript, and React experience",
            "jd_keywords": ["python", "javascript", "react", "frontend"]
        }
    ]
    
    for scenario in scenarios:
        print(f"📊 {scenario['name']}:")
        newsletter_chunks = nm.get_relevant_content(['resume'], max_chunks=1)
        result = scorer.calculate_confidence_score(
            scenario['resume'], 
            scenario['jd_keywords'], 
            newsletter_chunks
        )
        
        print(f"   JD-Resume Overlap: {result['jd_resume_overlap']:.1f}%")
        print(f"   Newsletter Relevance: {result['newsletter_relevance']:.1f}%")
        print(f"   Confidence Score: {result['confidence_score']}/100")
        print()

def demo_newsletter_content():
    """Demonstrate newsletter content retrieval."""
    print("\n📰 Newsletter Content Demo\n")
    
    nm = NewsletterManager()
    
    # Show available content
    print("📚 Available Newsletter Content:")
    print("=" * 50)
    for chunk in nm.chunks:
        print(f"📄 Article: {chunk.article_name}")
        print(f"🏷️  Topics: {', '.join(chunk.topics)}")
        print(f"📏 Content Length: {len(chunk.content)} characters")
        print()
    
    # Test search functionality
    print("🔍 Content Search Examples:")
    print("=" * 50)
    search_terms = ["bullet points", "keywords", "customization", "interview"]
    
    for term in search_terms:
        results = nm.search_content(term, max_results=1)
        if results:
            print(f"✅ '{term}': Found {len(results)} result(s)")
        else:
            print(f"❌ '{term}': No results found")

def main():
    """Run the complete demonstration."""
    print("🚀 Newsletter-Grounded Resume Review System")
    print("=" * 60)
    
    try:
        demo_newsletter_content()
        demo_relevance_scoring()
        demo_newsletter_grounded_review()
        
        print("\n🎉 Demo Complete!")
        print("\n✅ System Features Demonstrated:")
        print("   - Newsletter content management and search")
        print("   - Relevance scoring with 70/30 formula")
        print("   - Newsletter-grounded review generation")
        print("   - WhatsApp message formatting")
        print("   - Authentic Aakash-voiced feedback")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main() 