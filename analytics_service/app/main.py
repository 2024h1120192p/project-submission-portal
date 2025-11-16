from fastapi import FastAPI, HTTPException
from libs.events.schemas import AnalyticsWindow
from .store import get_latest, get_history

app = FastAPI()

@app.get("/analytics/latest", response_model=AnalyticsWindow)
def latest():
    w = get_latest()
    if not w:
        raise HTTPException(status_code=404, detail="No analytics yet")
    return w

@app.get("/analytics/history", response_model=list[AnalyticsWindow])
def history():
    return get_history()
