from libs.events.schemas import Submission, PlagiarismResult
from config.logging import get_logger
import random

from .openai_client import get_openai_client

logger = get_logger(__name__)


async def run_plagiarism_pipeline(sub: Submission) -> PlagiarismResult:
    """Async plagiarism detection pipeline with OpenAI AI detection.
    
    Generates scores for:
    - internal_score: similarity with other submissions in database (stub)
    - external_score: similarity with external sources (stub)
    - ai_generated_probability: likelihood of AI generation (OpenAI or stub)
    - flagged_sections: suspicious text sections
    
    Also enriches with business logic:
    - severity: categorization based on internal score
    - requires_review: flag for manual review
    - ai_generated_likely: flag for likely AI generation
    """
    # Stub logic for plagiarism scores (internal/external)
    internal = random.random()  # Random float between 0.0 and 1.0
    external = random.random()
    flagged = ["stub-flag"]  # As per requirements
    
    # AI detection: Use OpenAI if available, otherwise fall back to random
    openai_client = get_openai_client()
    ai_prob = random.random()  # Default fallback
    
    if sub.text and openai_client.enabled:
        try:
            logger.info(f"Running OpenAI AI detection for submission {sub.id}")
            ai_result = await openai_client.detect_ai_content(sub.text)
            
            if ai_result.get("openai_used", False):
                ai_prob = ai_result.get("ai_probability", ai_prob)
                
                # Add AI detection indicators to flagged sections
                indicators = ai_result.get("indicators", [])
                if indicators:
                    flagged.extend([f"ai-indicator: {ind}" for ind in indicators[:3]])
                
                logger.info(f"OpenAI detection complete: ai_probability={ai_prob}")
            else:
                logger.debug("OpenAI not used, falling back to random AI probability")
        except Exception as e:
            logger.warning(f"OpenAI detection failed: {e}, using random fallback")
    
    # Business logic: categorize severity
    if internal >= 0.7:
        severity = "high"
    elif internal >= 0.4:
        severity = "medium"
    else:
        severity = "low"
    
    # Business logic: flag for review (based on plagiarism OR AI detection)
    requires_review = internal >= 0.5 or ai_prob >= 0.7
    
    # Business logic: AI detection
    ai_generated_likely = ai_prob >= 0.7

    return PlagiarismResult(
        submission_id=sub.id,
        internal_score=internal,
        external_score=external,
        ai_generated_probability=ai_prob,
        flagged_sections=flagged,
        severity=severity,
        requires_review=requires_review,
        ai_generated_likely=ai_generated_likely,
    )
