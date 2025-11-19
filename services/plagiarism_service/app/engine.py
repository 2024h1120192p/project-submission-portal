from libs.events.schemas import Submission, PlagiarismResult
import random


async def run_plagiarism_pipeline(sub: Submission) -> PlagiarismResult:
    """Async plagiarism detection pipeline with stub logic.
    
    Generates random scores for:
    - internal_score: similarity with other submissions in database
    - external_score: similarity with external sources
    - ai_generated_probability: likelihood of AI generation
    - flagged_sections: suspicious text sections
    
    Also enriches with business logic:
    - severity: categorization based on internal score
    - requires_review: flag for manual review
    - ai_generated_likely: flag for likely AI generation
    """
    # Stub logic: generate random values
    internal = random.random()  # Random float between 0.0 and 1.0
    external = random.random()
    ai_prob = random.random()
    flagged = ["stub-flag"]  # As per requirements
    
    # Business logic: categorize severity
    if internal >= 0.7:
        severity = "high"
    elif internal >= 0.4:
        severity = "medium"
    else:
        severity = "low"
    
    # Business logic: flag for review
    requires_review = internal >= 0.5
    
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
