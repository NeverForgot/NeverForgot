from fastapi import FastAPI

from trakist.api.routes import businesses, health, live, reports, signals

app = FastAPI(title="Trakist API", version="0.1.0")

app.include_router(health.router)
app.include_router(businesses.router)
app.include_router(signals.router)
app.include_router(live.router)
app.include_router(reports.router)
