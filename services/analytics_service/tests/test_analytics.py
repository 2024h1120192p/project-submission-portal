from fastapi.testclient import TestClient
from services.analytics_service.app.main import app
from services.analytics_service.app.store import add_window
from datetime import datetime, timezone
from libs.events.schemas import AnalyticsWindow

client = TestClient(app)

def test_latest_and_history():
    add_window(
        AnalyticsWindow(
            timestamp=datetime.now(timezone.utc),
            submission_rate=12.0,
            avg_plagiarism=0.33,
            avg_ai_probability=0.21,
            spike_detected=False,
        )
    )

    r_latest = client.get("/analytics/latest")
    assert r_latest.status_code == 200

    r_hist = client.get("/analytics/history")
    assert r_hist.status_code == 200
    assert len(r_hist.json()) >= 1
