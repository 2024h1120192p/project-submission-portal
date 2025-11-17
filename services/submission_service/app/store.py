from libs.events.schemas import Submission

class SubmissionStore:
    def __init__(self):
        self.db = {}

    def save(self, sub: Submission):
        self.db[sub.id] = sub

    def get(self, sub_id: str) -> Submission:
        return self.db.get(sub_id)

    def get_by_user(self, user_id: str):
        return [s for s in self.db.values() if s.user_id == user_id]
