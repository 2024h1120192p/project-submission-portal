from libs.events.schemas import Submission, PlagiarismResult

def run_plagiarism_pipeline(sub: Submission) -> PlagiarismResult:
    internal = 0.42
    external = 0.13
    ai_prob = 0.37
    flagged = ["Stub section A", "Stub section B"]

    return PlagiarismResult(
        submission_id=sub.id,
        internal_score=internal,
        external_score=external,
        ai_generated_probability=ai_prob,
        flagged_sections=flagged,
    )
