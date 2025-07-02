"""
Relevance Scoring Engine
Calculates confidence scores based on JD-resume overlap and newsletter relevance.
"""

import re
import math
from typing import Dict, List, Set, Tuple, Any
from collections import Counter
from .newsletter_manager import NewsletterManager, NewsletterChunk

class RelevanceScorer:
    """Calculates relevance scores for resume-JD matching using newsletter content."""
    
    def __init__(self, newsletter_manager: NewsletterManager):
        """
        Initialize the relevance scorer.
        
        Args:
            newsletter_manager: Instance of NewsletterManager for content retrieval
        """
        self.newsletter_manager = newsletter_manager
        
        # Common stop words to exclude from scoring
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'a', 'an', 'as', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'is', 'am'
        }
    
    def calculate_confidence_score(self, resume_text: str, jd_keywords: List[str], 
                                 relevant_newsletter_chunks: List[NewsletterChunk]) -> Dict[str, Any]:
        """
        Calculate the overall confidence score using the 70/30 weighting formula.
        
        Args:
            resume_text: The extracted resume text
            jd_keywords: Keywords extracted from job description
            relevant_newsletter_chunks: Relevant newsletter content chunks
        
        Returns:
            Dict containing detailed scoring information
        """
        # Extract keywords from resume
        resume_keywords = self._extract_keywords_from_text(resume_text)
        
        # Calculate JD-Resume overlap score (70% weight)
        jd_resume_score = self._calculate_keyword_overlap_score(resume_keywords, jd_keywords)
        
        # Calculate newsletter relevance score (30% weight)
        newsletter_score = self._calculate_newsletter_relevance_score(
            resume_keywords, jd_keywords, relevant_newsletter_chunks
        )
        
        # Adjust scoring when no job URL is provided
        if not jd_keywords:
            # When no JD provided, focus more on newsletter relevance
            # Give a base score for having a resume that can be reviewed
            base_score = 0.3  # 30% base confidence for having a reviewable resume
            newsletter_weight = 0.7  # 70% weight on newsletter relevance
            final_score = base_score + (newsletter_score * newsletter_weight)
        else:
            # Standard 70/30 weighting when JD is provided
            final_score = (jd_resume_score * 0.7) + (newsletter_score * 0.3)
        
        # Convert to 0-100 scale
        confidence_score = int(round(final_score * 100))
        
        return {
            'job_fit_score': confidence_score,  # Renamed for clarity
            'confidence_score': confidence_score,  # Keep for backward compatibility
            'jd_resume_overlap': round(jd_resume_score * 100, 1),
            'newsletter_relevance': round(newsletter_score * 100, 1),
            'resume_keywords_count': len(resume_keywords),
            'jd_keywords_count': len(jd_keywords),
            'matching_keywords': self._find_matching_keywords(resume_keywords, jd_keywords),
            'newsletter_chunks_used': len(relevant_newsletter_chunks),
            'scoring_breakdown': {
                'jd_resume_weight': 70,
                'newsletter_weight': 30,
                'jd_resume_score': round(jd_resume_score, 3),
                'newsletter_score': round(newsletter_score, 3),
                'weighted_final': round(final_score, 3)
            }
        }
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Input text to extract keywords from
        
        Returns:
            List of extracted keywords
        """
        if not text:
            return []
        
        # Convert to lowercase and extract words
        text = text.lower()
        
        # Extract words (3+ characters, alphanumeric)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        
        # Remove stop words
        keywords = [word for word in words if word not in self.stop_words]
        
        # Count frequency and keep unique words
        word_counts = Counter(keywords)
        
        # Return words sorted by frequency (most common first)
        return [word for word, count in word_counts.most_common()]
    
    def _calculate_keyword_overlap_score(self, resume_keywords: List[str], jd_keywords: List[str]) -> float:
        """
        Calculate keyword overlap score between resume and job description.
        
        Args:
            resume_keywords: Keywords from resume
            jd_keywords: Keywords from job description
        
        Returns:
            Overlap score (0.0 to 1.0)
        """
        if not resume_keywords or not jd_keywords:
            return 0.0
        
        # Convert to sets for intersection
        resume_set = set(kw.lower() for kw in resume_keywords)
        jd_set = set(kw.lower() for kw in jd_keywords)
        
        # Calculate Jaccard similarity (intersection / union)
        intersection = len(resume_set & jd_set)
        union = len(resume_set | jd_set)
        
        if union == 0:
            return 0.0
        
        jaccard_score = intersection / union
        
        # Also calculate coverage score (how many JD keywords are covered)
        coverage_score = intersection / len(jd_set) if jd_set else 0.0
        
        # Combine both scores with equal weight
        final_score = (jaccard_score * 0.5) + (coverage_score * 0.5)
        
        return min(final_score, 1.0)
    
    def _calculate_newsletter_relevance_score(self, resume_keywords: List[str], 
                                           jd_keywords: List[str], 
                                           newsletter_chunks: List[NewsletterChunk]) -> float:
        """
        Calculate how relevant and comprehensive the newsletter content is for this review.
        
        Args:
            resume_keywords: Keywords from resume
            jd_keywords: Keywords from job description
            newsletter_chunks: Relevant newsletter content chunks
        
        Returns:
            Newsletter relevance score (0.0 to 1.0)
        """
        if not newsletter_chunks:
            return 0.0
        
        # Newsletter relevance should measure:
        # 1. How much newsletter content is available
        # 2. How comprehensive the guidance is
        # 3. How well it covers resume review topics
        
        # Base score for having newsletter content
        base_score = 0.3
        
        # Bonus for comprehensive content (more chunks = better guidance)
        content_bonus = min(len(newsletter_chunks) * 0.2, 0.4)  # Max 0.4 bonus
        
        # Bonus for content that covers resume review topics
        resume_review_topics = ['resume', 'interview', 'customization', 'bullet points', 'keywords']
        topic_coverage = 0.0
        
        for chunk in newsletter_chunks:
            chunk_topics = [topic.lower() for topic in chunk.topics]
            for topic in resume_review_topics:
                if topic in chunk_topics:
                    topic_coverage += 0.1
        
        topic_bonus = min(topic_coverage, 0.3)  # Max 0.3 bonus
        
        total_score = base_score + content_bonus + topic_bonus
        return min(total_score, 1.0)
    
    def _find_matching_keywords(self, resume_keywords: List[str], jd_keywords: List[str]) -> List[str]:
        """
        Find keywords that match between resume and JD.
        
        Args:
            resume_keywords: Keywords from resume
            jd_keywords: Keywords from job description
        
        Returns:
            List of matching keywords
        """
        resume_set = set(kw.lower() for kw in resume_keywords)
        jd_set = set(kw.lower() for kw in jd_keywords)
        
        return list(resume_set & jd_set)
    
    def get_content_recommendations(self, resume_text: str, jd_keywords: List[str], 
                                  confidence_score: int) -> Dict[str, Any]:
        """
        Get content recommendations based on scoring analysis.
        
        Args:
            resume_text: The resume text
            jd_keywords: Keywords from job description
            confidence_score: Calculated confidence score
        
        Returns:
            Dict containing content recommendations
        """
        recommendations = {
            'priority': 'medium',
            'suggested_improvements': [],
            'newsletter_sections_to_focus': [],
            'missing_keywords': []
        }
        
        # Set priority based on confidence score
        if confidence_score >= 80:
            recommendations['priority'] = 'low'
        elif confidence_score >= 60:
            recommendations['priority'] = 'medium'
        else:
            recommendations['priority'] = 'high'
        
        # Find missing keywords
        resume_keywords = self._extract_keywords_from_text(resume_text)
        missing_keywords = [kw for kw in jd_keywords if kw.lower() not in [rk.lower() for rk in resume_keywords]]
        recommendations['missing_keywords'] = missing_keywords[:10]  # Top 10 missing
        
        # Get relevant newsletter content for suggestions
        relevant_chunks = self.newsletter_manager.get_relevant_content(jd_keywords, max_chunks=3)
        
        if relevant_chunks:
            recommendations['newsletter_sections_to_focus'] = [
                {
                    'section': chunk.section,
                    'article': chunk.article_name,
                    'relevance_topics': chunk.topics
                }
                for chunk in relevant_chunks
            ]
        
        # Generate improvement suggestions based on score
        if confidence_score < 70:
            recommendations['suggested_improvements'].extend([
                "Incorporate more keywords from the job description",
                "Align experience descriptions with newsletter principles",
                "Quantify achievements where possible"
            ])
        
        if missing_keywords:
            recommendations['suggested_improvements'].append(
                f"Consider adding these relevant keywords: {', '.join(missing_keywords[:5])}"
            )
        
        return recommendations
    
    def analyze_resume_strengths(self, resume_text: str, newsletter_chunks: List[NewsletterChunk]) -> List[str]:
        """
        Analyze resume strengths based on newsletter content.
        
        Args:
            resume_text: The resume text
            newsletter_chunks: Relevant newsletter chunks
        
        Returns:
            List of identified strengths
        """
        strengths = []
        
        if not newsletter_chunks:
            return ["Strong professional experience", "Clear career progression"]
        
        resume_keywords = self._extract_keywords_from_text(resume_text)
        
        for chunk in newsletter_chunks:
            chunk_keywords = self._extract_keywords_from_text(chunk.content)
            
            # Find overlapping concepts
            overlap = set(kw.lower() for kw in resume_keywords) & set(kw.lower() for kw in chunk_keywords)
            
            if overlap and len(overlap) > 2:
                strengths.append(f"Demonstrates {chunk.section.lower()} principles")
        
        # Generic strengths if no specific matches
        if not strengths:
            strengths = [
                "Shows relevant professional experience",
                "Demonstrates career growth and development"
            ]
        
        return strengths[:4]  # Limit to top 4 strengths
    
    def identify_improvement_areas(self, resume_text: str, jd_keywords: List[str], 
                                 newsletter_chunks: List[NewsletterChunk]) -> List[Dict[str, str]]:
        """
        Identify areas for improvement based on newsletter content.
        
        Args:
            resume_text: The resume text
            jd_keywords: Keywords from job description
            newsletter_chunks: Relevant newsletter chunks
        
        Returns:
            List of improvement areas with citations
        """
        improvements = []
        
        if not newsletter_chunks:
            return [{"area": "General resume optimization needed", "citation": "General best practices"}]
        
        resume_keywords = self._extract_keywords_from_text(resume_text)
        missing_jd_keywords = [kw for kw in jd_keywords if kw.lower() not in [rk.lower() for rk in resume_keywords]]
        
        for chunk in newsletter_chunks:
            chunk_keywords = self._extract_keywords_from_text(chunk.content)
            
            # Check if this chunk addresses missing keywords
            chunk_addresses_missing = any(kw.lower() in [ck.lower() for ck in chunk_keywords] 
                                        for kw in missing_jd_keywords[:5])
            
            if chunk_addresses_missing:
                improvements.append({
                    "area": f"Better alignment with {chunk.section.lower()} principles",
                    "citation": f"{chunk.article_name} - {chunk.section}"
                })
        
        # Add generic improvements if none found
        if not improvements:
            improvements = [
                {
                    "area": "Incorporate more job-specific keywords",
                    "citation": "Resume customization best practices"
                },
                {
                    "area": "Quantify achievements and impact",
                    "citation": "Professional resume standards"
                }
            ]
        
        return improvements[:3]  # Limit to top 3 improvements
    
    def calculate_keyword_density(self, text: str, keywords: List[str]) -> Dict[str, float]:
        """
        Calculate keyword density in text.
        
        Args:
            text: Text to analyze
            keywords: Keywords to check for
        
        Returns:
            Dict mapping keywords to their density scores
        """
        if not text or not keywords:
            return {}
        
        text_lower = text.lower()
        text_words = len(text_lower.split())
        
        densities = {}
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            density = count / text_words if text_words > 0 else 0.0
            densities[keyword] = density
        
        return densities
    
    def suggest_newsletter_content(self, jd_keywords: List[str], max_suggestions: int = 5) -> List[NewsletterChunk]:
        """
        Suggest relevant newsletter content based on JD keywords.
        
        Args:
            jd_keywords: Keywords from job description
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List of suggested newsletter chunks
        """
        return self.newsletter_manager.get_relevant_content(jd_keywords, max_chunks=max_suggestions) 