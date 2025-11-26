from libs.events.schemas import Submission, PlagiarismResult
import random
import openai
from config.settings import get_settings
from config.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

async def run_plagiarism_pipeline(sub: Submission) -> PlagiarismResult:
    """Async plagiarism detection pipeline with OpenAI integration.
    
    Generates scores for:
    - internal_score: similarity with other submissions in database (stubbed)
    - external_score: similarity with external sources (stubbed)
    - ai_generated_probability: likelihood of AI generation (via OpenAI)
    - flagged_sections: suspicious text sections
    
    Also enriches with business logic:
    - severity: categorization based on internal score
    - requires_review: flag for manual review
    - ai_generated_likely: flag for likely AI generation
    """
    # Default stub values
    internal = random.random()
    external = random.random()
    ai_prob = random.random()
    flagged = ["stub-flag"]

    # Try OpenAI for AI detection if key is configured
    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-..."):
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI plagiarism detector. Analyze the following text and provide a JSON response with 'ai_probability' (0.0 to 1.0) and 'flagged_sections' (list of strings)."},
                    {"role": "user", "content": sub.text[:4000]}  # Limit text length
                ],
                response_format={"type": "json_object"}
            )
            import json
            content = json.loads(response.choices[0].message.content)
            ai_prob = content.get("ai_probability", ai_prob)
            flagged = content.get("flagged_sections", flagged)
            logger.info(f"OpenAI check successful for submission {sub.id}")
        except Exception as e:
            logger.error(f"OpenAI check failed: {e}")

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
