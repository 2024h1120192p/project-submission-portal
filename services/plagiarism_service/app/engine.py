from libs.events.schemas import Submission, PlagiarismResult
import random


async def run_plagiarism_pipeline(sub: Submission) -> PlagiarismResult:
    """Async plagiarism detection pipeline with stub logic.
    
    Generates random scores for:
    - internal_score: similarity with other submissions in database
    - external_score: similarity with external sources
    - ai_generated_probability: likelihood of AI generation
    - flagged_sections: suspicious text sections
    """
    # Stub logic: generate random values
    internal = random.random()  # Random float between 0.0 and 1.0
    external = random.random()
    ai_prob = random.random()
    flagged = ["stub-flag"]  # As per requirements

    return PlagiarismResult(
        submission_id=sub.id,
        internal_score=internal,
        external_score=external,
        ai_generated_probability=ai_prob,
        flagged_sections=flagged,
    )
