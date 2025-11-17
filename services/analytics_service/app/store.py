from datetime import datetime, timezone
from libs.events.schemas import AnalyticsWindow

# In-memory Firestore simulation
ANALYTICS_DB: list[AnalyticsWindow] = []

def add_window(window: AnalyticsWindow):
    ANALYTICS_DB.append(window)

def get_latest() -> AnalyticsWindow | None:
    if not ANALYTICS_DB:
        return None
    return ANALYTICS_DB[-1]

def get_history() -> list[AnalyticsWindow]:
    return ANALYTICS_DB
