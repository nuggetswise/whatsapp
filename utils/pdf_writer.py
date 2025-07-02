import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from typing import Dict, List, Any
import uuid

class ResumePDFWriter:
    def __init__(self, output_dir: str = "static"):
        """
        Initialize the PDF writer.
        
        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the resume."""
        # Header style
        self.styles.add(ParagraphStyle(
            name='ResumeHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=12,
            textColor=colors.HexColor('#2E86AB'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#2E86AB'),
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#2E86AB'),
            borderPadding=5,
            backColor=colors.HexColor('#F8F9FA')
        ))
        
        # Job title style
        self.styles.add(ParagraphStyle(
            name='JobTitle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=4,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#495057')
        ))
        
        # Company style
        self.styles.add(ParagraphStyle(
            name='Company',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=2,
            fontName='Helvetica',
            textColor=colors.HexColor('#6C757D')
        ))
        
        # Date style
        self.styles.add(ParagraphStyle(
            name='Date',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#6C757D'),
            alignment=TA_RIGHT
        ))
        
        # Bullet point style
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            fontName='Helvetica',
            textColor=colors.HexColor('#212529')
        ))
        
        # Citation style
        self.styles.add(ParagraphStyle(
            name='Citation',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#6C757D'),
            leftIndent=10
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=0,
            fontName='Helvetica',
            textColor=colors.HexColor('#6C757D'),
            alignment=TA_CENTER
        ))
    
    def _extract_rewritten_bullets(self, feedback: str) -> List[str]:
        """Extract rewritten bullets from the AI feedback."""
        bullets = []
        
        # Look for bullet points in the feedback
        lines = feedback.split('\n')
        in_bullet_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check if we're in a bullet section
            if 'rewritten bullets' in line.lower() or 'improved bullets' in line.lower():
                in_bullet_section = True
                continue
            
            # Check if we've moved to a new section
            if line.startswith('##') and in_bullet_section:
                break
            
            # Extract bullet points
            if in_bullet_section and line:
                # Remove common bullet markers
                clean_line = line.lstrip('•-*→➤')
                clean_line = clean_line.strip()
                
                if clean_line and len(clean_line) > 20:  # Meaningful content
                    bullets.append(clean_line)
        
        # If no bullets found in structured format, try to extract from general text
        if not bullets:
            # Look for lines that might be bullet points
            for line in lines:
                line = line.strip()
                if (line.startswith('•') or line.startswith('-') or 
                    (len(line) > 30 and any(word in line.lower() for word in ['improved', 'enhanced', 'optimized', 'increased', 'developed', 'led', 'managed']))):
                    clean_line = line.lstrip('•-*→➤')
                    clean_line = clean_line.strip()
                    if clean_line and len(clean_line) > 20:
                        bullets.append(clean_line)
        
        return bullets[:10]  # Limit to 10 bullets
    
    def _extract_assessment(self, feedback: str) -> str:
        """Extract the overall assessment from the feedback."""
        lines = feedback.split('\n')
        assessment_lines = []
        in_assessment = False
        
        for line in lines:
            line = line.strip()
            
            if 'overall assessment' in line.lower():
                in_assessment = True
                continue
            
            if line.startswith('##') and in_assessment:
                break
            
            if in_assessment and line:
                assessment_lines.append(line)
        
        return ' '.join(assessment_lines) if assessment_lines else "Resume review completed with AI-powered insights."
    
    def generate_resume_pdf(self, feedback: str, citations: List[Dict], metadata: Dict[str, Any]) -> str:
        """
        Generate a PDF resume with the rewritten bullets and citations.
        
        Args:
            feedback: The AI-generated feedback
            citations: List of citation dictionaries
            metadata: Additional metadata (phone, timestamp, etc.)
        
        Returns:
            Path to the generated PDF file
        """
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_optimized_{timestamp}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        
        # Header
        story.append(Paragraph("AI-Optimized Resume", self.styles['ResumeHeader']))
        story.append(Spacer(1, 20))
        
        # Assessment section
        assessment = self._extract_assessment(feedback)
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Paragraph(assessment, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Rewritten bullets section
        story.append(Paragraph("Optimized Experience Bullets", self.styles['SectionHeader']))
        
        bullets = self._extract_rewritten_bullets(feedback)
        if bullets:
            for bullet in bullets:
                story.append(Paragraph(f"• {bullet}", self.styles['BulletPoint']))
        else:
            story.append(Paragraph("AI-generated improvements will be applied to your resume bullets.", self.styles['BulletPoint']))
        
        story.append(Spacer(1, 20))
        
        # Citations section
        if citations:
            story.append(Paragraph("Expert Sources", self.styles['SectionHeader']))
            for citation in citations:
                citation_text = f"• {citation.get('title', 'Expert Source')}"
                if citation.get('url'):
                    citation_text += f" - {citation['url']}"
                story.append(Paragraph(citation_text, self.styles['Citation']))
            story.append(Spacer(1, 20))
        
        # Footer with metadata
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        if metadata.get('creator'):
            footer_text += f" | Powered by {metadata['creator']}'s expertise"
        if metadata.get('phone'):
            footer_text += f" | Requested via WhatsApp: {metadata['phone']}"
        
        story.append(Paragraph(footer_text, self.styles['Footer']))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def get_public_url(self, filepath: str, base_url: str = None) -> str:
        """
        Get the public URL for the generated PDF.
        
        Args:
            filepath: Path to the PDF file
            base_url: Base URL for the static files (optional)
        
        Returns:
            Public URL for the PDF
        """
        if base_url:
            filename = os.path.basename(filepath)
            return f"{base_url.rstrip('/')}/{filename}"
        else:
            return filepath
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old PDF files to save storage.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
        """
        try:
            current_time = datetime.now()
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.pdf'):
                    filepath = os.path.join(self.output_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                        os.remove(filepath)
                        print(f"Cleaned up old file: {filename}")
        except Exception as e:
            print(f"Error cleaning up old files: {e}")

def create_resume_pdf(feedback: str, citations: List[Dict], metadata: Dict[str, Any], output_dir: str = "static") -> Dict[str, Any]:
    """
    Convenience function to create a resume PDF.
    
    Args:
        feedback: The AI-generated feedback
        citations: List of citation dictionaries
        metadata: Additional metadata
        output_dir: Directory to save the PDF
    
    Returns:
        Dict containing filepath and public URL
    """
    writer = ResumePDFWriter(output_dir)
    
    # Clean up old files
    writer.cleanup_old_files()
    
    # Generate PDF
    filepath = writer.generate_resume_pdf(feedback, citations, metadata)
    
    return {
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2)
    } 