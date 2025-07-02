"""
Newsletter Management System
Stores and retrieves newsletter content with chunking and citation tracking.
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class NewsletterChunk:
    """Represents a chunk of newsletter content with metadata."""
    content: str
    article_name: str
    section: str
    topics: List[str]
    chunk_id: str
    created_at: str

class NewsletterManager:
    """Manages newsletter content storage, retrieval, and citation tracking."""
    
    def __init__(self, storage_path: str = "newsletter_content.json"):
        """
        Initialize the newsletter manager.
        
        Args:
            storage_path: Path to store newsletter content
        """
        self.storage_path = storage_path
        self.chunks: List[NewsletterChunk] = []
        self.load_content()
        
        # If no content exists, load the default Aakash article
        if not self.chunks:
            self._load_default_content()
    
    def _load_default_content(self):
        """Load the default Aakash newsletter content."""
        default_content = """
        # How to Customize Your Resume to Actually Get Interviews
        
        The #1 mistake people make in trying to get interviews? Sharing a generic resume or customizing poorly. There are 6 key principles of customization:

        ## 1. Recast Your Experience to Become Ideal
        Ask "What archetypes of person would the hiring manager be ecstatic to hire?" Then re-cast as many details as possible to become that person.
        
        ## 2. Re-tell Your Story to Be a Straight Line
        Make your winding path seem like a straight line to the job. Remove or minimize jobs that don't fit the archetype.
        
        ## 3. Customize Every Bullet for the Job
        If bullet points aren't positioning you for the job, the space can be better used. Developer experience might be more exciting than activation lift for internal tools roles.
        
        ## 4. Use the Keywords the ATS Seeks
        AI Resume Screening systems look for keyword existence, not meaning. Cover all the bases the job description mentions.
        
        ## 5. Drop Examples to Intrigue
        Create a compelling reason to interview you. Drop enough storytelling so they want to follow-up.
        
        ## 6. Flip Your Weaknesses
        Identify common reasons you might get disqualified and flip them into strengths through narrative and bullet points.
        
        ## Additional Tips
        
        ### Resume Structure
        - Keep it concise but impactful
        - Use quantifiable achievements
        - Lead with action verbs
        - Maintain consistent formatting
        
        ### Tailoring Strategy
        - Research the company culture
        - Match their language and tone
        - Highlight relevant experience
        - Show progression and growth
        """
        
        self.add_article(
            content=default_content,
            article_name="How to Customize Your Resume to Actually Get Interviews",
            article_url="https://www.news.aakashg.com/p/how-to-customize-your-resume-to-actually"
        )
    
    def add_article(self, content: str, article_name: str, article_url: str = None) -> bool:
        """
        Add a new newsletter article with automatic chunking.
        
        Args:
            content: The article content
            article_name: Name of the article
            article_url: Optional URL of the article
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Chunk the content
            chunks = self._chunk_content(content, article_name)
            
            # Add chunks to storage
            for chunk in chunks:
                self.chunks.append(chunk)
            
            # Save to file
            self.save_content()
            
            return True
        except Exception as e:
            print(f"Error adding article: {e}")
            return False
    
    def _chunk_content(self, content: str, article_name: str) -> List[NewsletterChunk]:
        """
        Chunk content into logical sections.
        
        Args:
            content: The article content
            article_name: Name of the article
        
        Returns:
            List of NewsletterChunk objects
        """
        chunks = []
        
        # Split by sections (headers)
        sections = re.split(r'\n#{1,3}\s+', content)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            # Extract section title (first line)
            lines = section.strip().split('\n')
            section_title = lines[0] if lines else f"Section {i+1}"
            section_content = '\n'.join(lines[1:]) if len(lines) > 1 else lines[0]
            
            # Extract topics/keywords from the section
            topics = self._extract_topics(section_content)
            
            # Create chunk
            chunk = NewsletterChunk(
                content=section_content.strip(),
                article_name=article_name,
                section=section_title.strip(),
                topics=topics,
                chunk_id=f"{article_name.lower().replace(' ', '_')}_{i}",
                created_at=datetime.now().isoformat()
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _extract_topics(self, content: str) -> List[str]:
        """
        Extract topics/keywords from content.
        
        Args:
            content: The content to analyze
        
        Returns:
            List of extracted topics
        """
        # Simple keyword extraction
        keywords = [
            'resume', 'interview', 'job', 'experience', 'skills', 'keywords',
            'achievements', 'bullet points', 'customization', 'ATS', 'screening',
            'archetype', 'story', 'narrative', 'strengths', 'weaknesses'
        ]
        
        topics = []
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword in content_lower:
                topics.append(keyword)
        
        return topics
    
    def get_relevant_content(self, query_keywords: List[str], max_chunks: int = 5) -> List[NewsletterChunk]:
        """
        Get relevant newsletter content based on keywords.
        
        Args:
            query_keywords: List of keywords to search for
            max_chunks: Maximum number of chunks to return
        
        Returns:
            List of relevant NewsletterChunk objects
        """
        scored_chunks = []
        
        for chunk in self.chunks:
            score = self._calculate_relevance_score(chunk, query_keywords)
            if score > 0:
                scored_chunks.append((chunk, score))
        
        # Sort by score (descending) and return top chunks
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return [chunk for chunk, score in scored_chunks[:max_chunks]]
    
    def _calculate_relevance_score(self, chunk: NewsletterChunk, keywords: List[str]) -> float:
        """
        Calculate relevance score for a chunk based on keywords.
        
        Args:
            chunk: The newsletter chunk
            keywords: List of keywords to match
        
        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not keywords:
            return 0.0
        
        content_lower = chunk.content.lower()
        topic_matches = set(chunk.topics) & set(kw.lower() for kw in keywords)
        content_matches = sum(1 for kw in keywords if kw.lower() in content_lower)
        
        # Calculate score
        topic_score = len(topic_matches) / len(keywords) * 0.6
        content_score = min(content_matches / len(keywords), 1.0) * 0.4
        
        return topic_score + content_score
    
    def get_citation_info(self, chunk_id: str) -> Optional[Dict[str, str]]:
        """
        Get citation information for a chunk.
        
        Args:
            chunk_id: ID of the chunk
        
        Returns:
            Dict with citation info or None if not found
        """
        for chunk in self.chunks:
            if chunk.chunk_id == chunk_id:
                return {
                    "article_name": chunk.article_name,
                    "section": chunk.section,
                    "url": "https://www.news.aakashg.com/p/how-to-customize-your-resume-to-actually"
                }
        return None
    
    def get_all_content(self) -> str:
        """
        Get all newsletter content as a single string.
        
        Returns:
            Combined content from all chunks
        """
        content_parts = []
        current_article = None
        
        for chunk in self.chunks:
            if chunk.article_name != current_article:
                if current_article is not None:
                    content_parts.append("\n\n")
                content_parts.append(f"# {chunk.article_name}\n\n")
                current_article = chunk.article_name
            
            content_parts.append(f"## {chunk.section}\n{chunk.content}\n\n")
        
        return "".join(content_parts)
    
    def save_content(self) -> bool:
        """
        Save newsletter content to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "chunks": [
                    {
                        "content": chunk.content,
                        "article_name": chunk.article_name,
                        "section": chunk.section,
                        "topics": chunk.topics,
                        "chunk_id": chunk.chunk_id,
                        "created_at": chunk.created_at
                    }
                    for chunk in self.chunks
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving newsletter content: {e}")
            return False
    
    def load_content(self) -> bool:
        """
        Load newsletter content from file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.storage_path):
                return False
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.chunks = []
            for chunk_data in data.get("chunks", []):
                chunk = NewsletterChunk(
                    content=chunk_data["content"],
                    article_name=chunk_data["article_name"],
                    section=chunk_data["section"],
                    topics=chunk_data["topics"],
                    chunk_id=chunk_data["chunk_id"],
                    created_at=chunk_data["created_at"]
                )
                self.chunks.append(chunk)
            
            return True
        except Exception as e:
            print(f"Error loading newsletter content: {e}")
            return False
    
    def search_content(self, query: str, max_results: int = 3) -> List[Tuple[NewsletterChunk, float]]:
        """
        Search for content matching a query.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of (chunk, relevance_score) tuples
        """
        query_keywords = query.lower().split()
        scored_chunks = []
        
        for chunk in self.chunks:
            score = self._calculate_relevance_score(chunk, query_keywords)
            if score > 0:
                scored_chunks.append((chunk, score))
        
        # Sort by score and return top results
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return scored_chunks[:max_results] 