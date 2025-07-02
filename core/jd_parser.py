"""
Job Description Parser
Universal web scraper for job posting URLs that extracts structured information.
"""

import os
import re
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import json
import time

class JobDescriptionParser:
    """Universal job description parser for multiple platforms."""
    
    def __init__(self):
        """Initialize the parser with platform-specific handlers."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Platform-specific parsers
        self.parsers = {
            'linkedin.com': self._parse_linkedin,
            'indeed.com': self._parse_indeed,
            'glassdoor.com': self._parse_glassdoor,
            'greenhouse.io': self._parse_greenhouse,
            'lever.co': self._parse_lever,
            'workday.com': self._parse_workday,
            'bamboohr.com': self._parse_bamboohr,
            'smartrecruiters.com': self._parse_smartrecruiters,
            'default': self._parse_generic
        }
    
    def parse_job_url(self, url: str) -> Dict[str, Any]:
        """
        Parse a job URL and extract structured information.
        
        Args:
            url: The job posting URL
        
        Returns:
            Dict containing parsed job information
        """
        try:
            # Clean and validate URL
            cleaned_url = self._clean_url(url)
            if not cleaned_url:
                return self._create_error_result("Invalid URL provided")
            
            # Determine platform
            platform = self._identify_platform(cleaned_url)
            
            # Get the appropriate parser
            parser_func = self.parsers.get(platform, self.parsers['default'])
            
            # Parse the job description
            result = parser_func(cleaned_url)
            
            # Add metadata
            result['original_url'] = url
            result['cleaned_url'] = cleaned_url
            result['platform'] = platform
            result['parsed_at'] = time.time()
            
            return result
            
        except Exception as e:
            return self._create_error_result(f"Error parsing job URL: {str(e)}")
    
    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and validate the URL."""
        if not url or not isinstance(url, str):
            return None
        
        # Add https if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Clean common tracking parameters
        try:
            parsed = urlparse(url)
            
            # Remove common tracking parameters
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
                'ref', 'referer', 'referrer', 'source', 'src', 'fbclid', 'gclid'
            ]
            
            query_params = parse_qs(parsed.query)
            cleaned_params = {k: v for k, v in query_params.items() 
                            if k not in tracking_params}
            
            # Handle specific platform cleaning
            if 'greenhouse.io' in parsed.netloc and 'gh_src' in query_params:
                # Remove Greenhouse tracking
                cleaned_params = {k: v for k, v in cleaned_params.items() if k != 'gh_src'}
            
            # Rebuild URL
            from urllib.parse import urlencode, urlunparse
            cleaned_query = urlencode(cleaned_params, doseq=True)
            cleaned_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, cleaned_query, parsed.fragment
            ))
            
            return cleaned_url
            
        except Exception:
            return url
    
    def _identify_platform(self, url: str) -> str:
        """Identify the job platform from URL."""
        try:
            domain = urlparse(url).netloc.lower()
            
            for platform in self.parsers.keys():
                if platform != 'default' and platform in domain:
                    return platform
            
            return 'default'
        except Exception:
            return 'default'
    
    def _fetch_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse page content."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching page content: {e}")
            return None
    
    def _parse_linkedin(self, url: str) -> Dict[str, Any]:
        """Parse LinkedIn job posting."""
        soup = self._fetch_page_content(url)
        if not soup:
            return self._create_error_result("Could not fetch LinkedIn page")
        
        try:
            # Extract job title
            title_elem = soup.find('h1', class_='t-24') or soup.find('h1', {'data-test': 'job-title'})
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract company name
            company_elem = soup.find('a', class_='ember-view') or soup.find('span', class_='jobs-unified-top-card__company-name')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Extract job description
            desc_elem = soup.find('div', class_='jobs-description-content__text') or soup.find('div', {'data-test': 'job-description'})
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return self._create_success_result(title, company, description, self._extract_skills_from_text(description))
            
        except Exception as e:
            return self._create_error_result(f"Error parsing LinkedIn job: {str(e)}")
    
    def _parse_indeed(self, url: str) -> Dict[str, Any]:
        """Parse Indeed job posting."""
        soup = self._fetch_page_content(url)
        if not soup:
            return self._create_error_result("Could not fetch Indeed page")
        
        try:
            # Extract job title
            title_elem = soup.find('h1', {'data-testid': 'jobsearch-JobInfoHeader-title'}) or soup.find('h3', class_='jobsearch-JobInfoHeader-title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract company name
            company_elem = soup.find('div', {'data-testid': 'inlineHeader-companyName'}) or soup.find('span', class_='css-87z5no')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Extract job description
            desc_elem = soup.find('div', {'data-testid': 'jobsearch-jobDescriptionText'}) or soup.find('div', id='jobDescriptionText')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return self._create_success_result(title, company, description, self._extract_skills_from_text(description))
            
        except Exception as e:
            return self._create_error_result(f"Error parsing Indeed job: {str(e)}")
    
    def _parse_greenhouse(self, url: str) -> Dict[str, Any]:
        """Parse Greenhouse job posting."""
        soup = self._fetch_page_content(url)
        if not soup:
            return self._create_error_result("Could not fetch Greenhouse page")
        
        try:
            # Extract job title
            title_elem = soup.find('h1', class_='app-title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract company name (usually in the page title or header)
            company_elem = soup.find('span', class_='company-name') or soup.find('div', class_='header-company-name')
            if not company_elem:
                # Try to extract from title tag
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text()
                    # Pattern: "Job Title at Company Name"
                    if ' at ' in title_text:
                        company = title_text.split(' at ')[-1].strip()
                    else:
                        company = "Unknown"
                else:
                    company = "Unknown"
            else:
                company = company_elem.get_text(strip=True)
            
            # Extract job description - try multiple selectors based on Greenhouse structure
            desc_elem = (
                soup.find('div', class_='content') or 
                soup.find('div', id='content') or
                soup.find('div', class_='job-description') or
                soup.find('div', {'data-testid': 'job-description'}) or
                soup.find('div', class_='description') or
                soup.find('section', class_='content') or
                # Look for the main content area
                soup.find('div', class_='app-container') or
                soup.find('main')
            )
            
            if desc_elem:
                # Clean up the description by removing navigation and other non-content elements
                for elem in desc_elem.find_all(['nav', 'header', 'footer', 'script', 'style']):
                    elem.decompose()
                description = desc_elem.get_text(strip=True)
            else:
                description = ""
            
            return self._create_success_result(title, company, description, self._extract_skills_from_text(description))
            
        except Exception as e:
            return self._create_error_result(f"Error parsing Greenhouse job: {str(e)}")
    
    def _parse_lever(self, url: str) -> Dict[str, Any]:
        """Parse Lever job posting."""
        soup = self._fetch_page_content(url)
        if not soup:
            return self._create_error_result("Could not fetch Lever page")
        
        try:
            # Extract job title
            title_elem = soup.find('h2', {'data-qa': 'posting-name'}) or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract company name
            company_elem = soup.find('div', class_='posting-headline')
            if company_elem:
                company_link = company_elem.find('a')
                company = company_link.get_text(strip=True) if company_link else "Unknown"
            else:
                company = "Unknown"
            
            # Extract job description
            desc_elem = soup.find('div', class_='section-wrapper') or soup.find('div', {'data-qa': 'job-description'})
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return self._create_success_result(title, company, description, self._extract_skills_from_text(description))
            
        except Exception as e:
            return self._create_error_result(f"Error parsing Lever job: {str(e)}")
    
    def _parse_workday(self, url: str) -> Dict[str, Any]:
        """Parse Workday job posting."""
        soup = self._fetch_page_content(url)
        if not soup:
            return self._create_error_result("Could not fetch Workday page")
        
        try:
            # Workday often uses dynamic content, so we look for common patterns
            title_elem = soup.find('h1', {'data-automation-id': 'jobPostingHeader'}) or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Company name is often in the URL or page metadata
            company = self._extract_company_from_url(url) or "Unknown"
            
            # Extract job description
            desc_elem = soup.find('div', {'data-automation-id': 'jobPostingDescription'}) or soup.find('div', class_='jobdescription')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return self._create_success_result(title, company, description, self._extract_skills_from_text(description))
            
        except Exception as e:
            return self._create_error_result(f"Error parsing Workday job: {str(e)}")
    
    def _parse_bamboohr(self, url: str) -> Dict[str, Any]:
        """Parse BambooHR job posting."""
        return self._parse_generic(url)
    
    def _parse_smartrecruiters(self, url: str) -> Dict[str, Any]:
        """Parse SmartRecruiters job posting."""
        return self._parse_generic(url)
    
    def _parse_glassdoor(self, url: str) -> Dict[str, Any]:
        """Parse Glassdoor job posting."""
        return self._parse_generic(url)
    
    def _parse_generic(self, url: str) -> Dict[str, Any]:
        """Generic parser for unknown job platforms."""
        soup = self._fetch_page_content(url)
        if not soup:
            return self._create_error_result("Could not fetch page content")
        
        try:
            # Try common patterns for job title
            title_elem = (soup.find('h1') or 
                         soup.find('title') or
                         soup.find(attrs={'class': re.compile(r'job.*title|title.*job', re.I)}) or
                         soup.find(attrs={'id': re.compile(r'job.*title|title.*job', re.I)}))
            
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Try to extract company name
            company = (self._extract_company_from_url(url) or 
                      self._extract_company_from_page(soup) or 
                      "Unknown")
            
            # Extract full page text as description
            description = soup.get_text(strip=True)
            
            return self._create_success_result(title, company, description, self._extract_skills_from_text(description))
            
        except Exception as e:
            return self._create_error_result(f"Error parsing generic job page: {str(e)}")
    
    def _extract_company_from_url(self, url: str) -> Optional[str]:
        """Extract company name from URL patterns."""
        try:
            parsed = urlparse(url)
            
            # Pattern 1: subdomain (company.workday.com, company.greenhouse.io)
            if parsed.netloc.count('.') >= 2:
                company = parsed.netloc.split('.')[0]
                if company not in ['www', 'jobs', 'careers', 'apply']:
                    return company.replace('-', ' ').title()
            
            # Pattern 2: path-based (careers.company.com/job/...)
            path_parts = parsed.path.split('/')
            for part in path_parts:
                if len(part) > 2 and part not in ['job', 'jobs', 'career', 'careers', 'apply']:
                    return part.replace('-', ' ').replace('_', ' ').title()
            
            return None
        except Exception:
            return None
    
    def _extract_company_from_page(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from page content."""
        try:
            # Look for common company name patterns
            company_patterns = [
                {'class': re.compile(r'company.*name|employer.*name', re.I)},
                {'id': re.compile(r'company.*name|employer.*name', re.I)},
                {'data-testid': re.compile(r'company|employer', re.I)}
            ]
            
            for pattern in company_patterns:
                elem = soup.find(attrs=pattern)
                if elem:
                    return elem.get_text(strip=True)
            
            return None
        except Exception:
            return None
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills and qualifications from job description text."""
        if not text:
            return []
        
        # Common skill keywords for product management and tech roles
        skill_keywords = [
            # Product Management
            'product management', 'product strategy', 'roadmap', 'user research',
            'data analysis', 'A/B testing', 'metrics', 'KPIs', 'stakeholder management',
            'cross-functional', 'agile', 'scrum', 'user experience', 'UX', 'UI',
            'market research', 'competitive analysis', 'go-to-market', 'GTM',
            
            # Technical Skills
            'SQL', 'Python', 'JavaScript', 'React', 'API', 'REST', 'GraphQL',
            'machine learning', 'ML', 'AI', 'data science', 'analytics',
            'cloud', 'AWS', 'Azure', 'GCP', 'docker', 'kubernetes',
            
            # Soft Skills
            'leadership', 'communication', 'collaboration', 'problem solving',
            'critical thinking', 'strategic thinking', 'decision making',
            
            # Experience Levels
            'junior', 'senior', 'lead', 'principal', 'director', 'VP', 'head of',
            'manager', 'associate', 'intern', 'entry level', 'experienced'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Remove duplicates and return
        return list(set(found_skills))
    
    def _create_success_result(self, title: str, company: str, description: str, skills: List[str]) -> Dict[str, Any]:
        """Create a successful parsing result."""
        return {
            'success': True,
            'role_title': title,
            'company_name': company,
            'description': description,
            'key_qualifications': ', '.join(skills[:10]),  # Limit to top 10 skills
            'skills': skills,
            'error': None
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create an error result."""
        return {
            'success': False,
            'role_title': 'Unknown',
            'company_name': 'Unknown',
            'description': '',
            'key_qualifications': '',
            'skills': [],
            'error': error_message
        }
    
    def extract_keywords_for_matching(self, parsed_jd: Dict[str, Any]) -> List[str]:
        """
        Extract keywords from parsed job description for resume matching.
        
        Args:
            parsed_jd: Parsed job description dictionary
        
        Returns:
            List of keywords for matching
        """
        keywords = []
        
        # Add role title words
        if parsed_jd.get('role_title'):
            keywords.extend(parsed_jd['role_title'].lower().split())
        
        # Add skills
        if parsed_jd.get('skills'):
            keywords.extend([skill.lower() for skill in parsed_jd['skills']])
        
        # Add company name words
        if parsed_jd.get('company_name'):
            keywords.extend(parsed_jd['company_name'].lower().split())
        
        # Extract keywords from description
        if parsed_jd.get('description'):
            desc_keywords = self._extract_important_keywords(parsed_jd['description'])
            keywords.extend(desc_keywords)
        
        # Remove duplicates and common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        keywords = [kw for kw in set(keywords) if kw not in stop_words and len(kw) > 2]
        
        return keywords
    
    def _extract_important_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract important keywords from text using simple frequency analysis."""
        if not text:
            return []
        
        # Simple tokenization and frequency counting
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:max_keywords]] 