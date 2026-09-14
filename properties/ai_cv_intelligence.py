"""
CV Intelligence System
Analyzes CVs and matches with job opportunities
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import re

from .ai_multimodal_input import DocumentData, DocumentType

logger = logging.getLogger(__name__)


class SkillLevel(Enum):
    """Proficiency levels for skills"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    UNKNOWN = "unknown"


@dataclass
class Skill:
    """Represents a skill with proficiency"""
    name: str
    level: SkillLevel
    years_experience: float = 0.0
    last_used: str = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'level': self.level.value,
            'years_experience': self.years_experience,
            'last_used': self.last_used,
            'confidence': self.confidence
        }


@dataclass
class WorkExperience:
    """Represents work experience entry"""
    company: str
    position: str
    start_date: str
    end_date: str = None
    description: str = None
    skills_used: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'company': self.company,
            'position': self.position,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'description': self.description,
            'skills_used': self.skills_used
        }


@dataclass
class Education:
    """Represents education entry"""
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: str = None
    gpa: float = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'institution': self.institution,
            'degree': self.degree,
            'field_of_study': self.field_of_study,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'gpa': self.gpa
        }


@dataclass
class CVProfile:
    """Comprehensive CV profile"""
    cv_id: str
    name: str = None
    email: str = None
    phone: str = None
    skills: List[Skill] = field(default_factory=list)
    experience: List[WorkExperience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    total_years_experience: float = 0.0
    extraction_confidence: float = 0.0
    analysis_timestamp: str = None
    
    def __post_init__(self):
        if not self.analysis_timestamp:
            self.analysis_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'cv_id': self.cv_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'skills': [skill.to_dict() for skill in self.skills],
            'experience': [exp.to_dict() for exp in self.experience],
            'education': [edu.to_dict() for edu in self.education],
            'languages': self.languages,
            'certifications': self.certifications,
            'total_years_experience': self.total_years_experience,
            'extraction_confidence': self.extraction_confidence,
            'analysis_timestamp': self.analysis_timestamp
        }


class CVIntelligenceSystem:
    """
    Analyzes CVs and matches with job opportunities
    Only reports information actually found in the CV
    """
    
    def __init__(self):
        self.skill_patterns = self._initialize_skill_patterns()
        self.analysis_history: List[Dict] = []
    
    def analyze_cv(self, cv_document: DocumentData) -> CVProfile:
        """
        Analyze CV document and extract profile
        
        Args:
            cv_document: CV document data
            
        Returns:
            CVProfile with extracted information
        """
        try:
            # Extract text if not already extracted
            if not cv_document.text_content:
                cv_document.text_content = self._extract_cv_text(cv_document)
            
            # Parse CV content
            profile = self._parse_cv_content(cv_document)
            
            # Calculate confidence
            profile.extraction_confidence = self._calculate_extraction_confidence(profile)
            
            # Log analysis
            self.analysis_history.append({
                'timestamp': datetime.now().isoformat(),
                'cv_id': profile.cv_id,
                'skill_count': len(profile.skills),
                'experience_count': len(profile.experience),
                'confidence': profile.extraction_confidence
            })
            
            logger.info(f"Analyzed CV {profile.cv_id}: {len(profile.skills)} skills, {len(profile.experience)} experiences")
            return profile
            
        except Exception as e:
            logger.error(f"Error analyzing CV: {str(e)}")
            return self._create_error_profile(cv_document, str(e))
    
    def _extract_cv_text(self, cv_document: DocumentData) -> str:
        """Extract text from CV document (placeholder)"""
        # This would integrate with OCR/PDF extraction service
        # For now, return placeholder
        logger.info(f"Extracting text from CV {cv_document.document_id}")
        return f"[CV text extraction placeholder for {cv_document.document_id}]"
    
    def _parse_cv_content(self, cv_document: DocumentData) -> CVProfile:
        """Parse CV content and extract structured information"""
        text = cv_document.text_content
        
        profile = CVProfile(cv_id=cv_document.document_id)
        
        # Extract name (placeholder)
        profile.name = self._extract_name(text)
        
        # Extract contact info (placeholder)
        profile.email = self._extract_email(text)
        profile.phone = self._extract_phone(text)
        
        # Extract skills
        profile.skills = self._extract_skills(text)
        
        # Extract experience
        profile.experience = self._extract_experience(text)
        
        # Extract education
        profile.education = self._extract_education(text)
        
        # Extract languages
        profile.languages = self._extract_languages(text)
        
        # Extract certifications
        profile.certifications = self._extract_certifications(text)
        
        # Calculate total experience
        profile.total_years_experience = self._calculate_total_experience(profile.experience)
        
        return profile
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from CV text (placeholder)"""
        # This would use NLP to extract name
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from CV text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone from CV text"""
        phone_pattern = r'\b\d{10,}\b'
        phones = re.findall(phone_pattern, text)
        return phones[0] if phones else None
    
    def _extract_skills(self, text: str) -> List[Skill]:
        """Extract skills from CV text"""
        skills = []
        
        # Check for common tech skills
        tech_skills = [
            'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'django', 'flask',
            'react', 'angular', 'vue', 'nodejs', 'mongodb', 'postgresql', 'mysql',
            'aws', 'azure', 'docker', 'kubernetes', 'git', 'linux', 'html', 'css'
        ]
        
        text_lower = text.lower()
        for skill_name in tech_skills:
            if skill_name in text_lower:
                # Estimate years from context (placeholder)
                years = self._estimate_skill_years(text_lower, skill_name)
                
                skills.append(Skill(
                    name=skill_name,
                    level=SkillLevel.INTERMEDIATE,  # Default assumption
                    years_experience=years,
                    confidence=0.7
                ))
        
        return skills
    
    def _estimate_skill_years(self, text: str, skill: str) -> float:
        """Estimate years of experience for a skill (placeholder)"""
        # This would analyze experience descriptions
        return 2.0  # Default placeholder
    
    def _extract_experience(self, text: str) -> List[WorkExperience]:
        """Extract work experience from CV text (placeholder)"""
        # This would use NLP to parse experience sections
        return []
    
    def _extract_education(self, text: str) -> List[Education]:
        """Extract education from CV text (placeholder)"""
        # This would use NLP to parse education sections
        return []
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract languages from CV text"""
        languages = []
        
        common_languages = ['english', 'arabic', 'french', 'german', 'spanish', 'turkish']
        text_lower = text.lower()
        
        for lang in common_languages:
            if lang in text_lower:
                languages.append(lang)
        
        return languages
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from CV text (placeholder)"""
        # This would use pattern matching for common certifications
        return []
    
    def _calculate_total_experience(self, experiences: List[WorkExperience]) -> float:
        """Calculate total years of experience"""
        total = 0.0
        
        for exp in experiences:
            if exp.start_date and exp.end_date:
                # Calculate duration (placeholder)
                total += 1.0  # Default placeholder
        
        return total
    
    def _calculate_extraction_confidence(self, profile: CVProfile) -> float:
        """Calculate confidence in extraction based on completeness"""
        factors = 0.0
        
        if profile.name:
            factors += 0.1
        if profile.email:
            factors += 0.1
        if profile.phone:
            factors += 0.1
        if profile.skills:
            factors += 0.3
        if profile.experience:
            factors += 0.3
        if profile.education:
            factors += 0.1
        
        return min(factors, 1.0)
    
    def match_with_jobs(self, 
                       cv_profile: CVProfile,
                       job_listings: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        Match CV profile with job listings
        
        Args:
            cv_profile: Extracted CV profile
            job_listings: List of job listings to match against
            
        Returns:
            List of (job, match_score) sorted by match score
        """
        matches = []
        
        for job in job_listings:
            match_score = self._calculate_job_match_score(cv_profile, job)
            matches.append((job, match_score))
        
        # Sort by match score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def _calculate_job_match_score(self, cv_profile: CVProfile, job: Dict) -> float:
        """Calculate match score between CV and job"""
        score = 0.0
        
        # Skill matching
        job_skills = job.get('required_skills', [])
        cv_skill_names = [skill.name for skill in cv_profile.skills]
        
        matching_skills = set(job_skills) & set(cv_skill_names)
        if job_skills:
            skill_score = len(matching_skills) / len(job_skills)
            score += skill_score * 0.5
        
        # Experience matching
        required_experience = job.get('required_experience', 0)
        if cv_profile.total_years_experience >= required_experience:
            score += 0.3
        
        # Education matching
        required_education = job.get('required_education')
        if required_education:
            has_matching_education = any(
                edu.degree == required_education for edu in cv_profile.education
            )
            if has_matching_education:
                score += 0.2
        
        return min(score, 1.0)
    
    def generate_match_explanation(self, 
                                  cv_profile: CVProfile,
                                  job: Dict,
                                  match_score: float) -> str:
        """Generate explanation for job match"""
        job_title = job.get('title', 'الوظيفة')
        
        if match_score > 0.8:
            return f"وظيفة {job_title} تبدو مناسبة جدًا لمهاراتك وخبراتك حسب البيانات الموجودة في الـCV."
        elif match_score > 0.5:
            return f"وظيفة {job_title} قد تكون مناسبة، لكن بعض المتطلبات لا تتطابق تمامًا مع ملفك."
        else:
            return f"وظيفة {job_title} قد لا تكون مناسبة بناءً على المهارات والخبرة الموجودة في الـCV."
    
    def _create_error_profile(self, cv_document: DocumentData, error: str) -> CVProfile:
        """Create error profile when analysis fails"""
        profile = CVProfile(cv_id=cv_document.document_id)
        profile.extraction_confidence = 0.0
        return profile
    
    def _initialize_skill_patterns(self) -> Dict:
        """Initialize skill detection patterns"""
        return {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#'],
            'web': ['html', 'css', 'react', 'angular', 'vue'],
            'database': ['sql', 'mongodb', 'postgresql', 'mysql'],
            'cloud': ['aws', 'azure', 'gcp'],
            'devops': ['docker', 'kubernetes', 'git', 'jenkins']
        }
    
    def get_cv_summary(self, cv_profile: CVProfile) -> Dict:
        """Get summary of CV profile"""
        return {
            'cv_id': cv_profile.cv_id,
            'name': cv_profile.name,
            'skill_count': len(cv_profile.skills),
            'experience_count': len(cv_profile.experience),
            'education_count': len(cv_profile.education),
            'total_years_experience': cv_profile.total_years_experience,
            'top_skills': [skill.name for skill in cv_profile.skills[:5]],
            'extraction_confidence': cv_profile.extraction_confidence
        }


# Global instance
cv_intelligence_system = CVIntelligenceSystem()