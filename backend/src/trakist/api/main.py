import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from trakist.api.routes import (
    admin,
    businesses,
    channels,
    health,
    ingestion,
    live,
    offers,
    products,
    reports,
    signals,
)
from trakist.config import get_settings
from trakist.scheduler import create_scheduler

# Sans ceci, les logger.info(...) des stubs WhatsApp/paiement (services/
# notification/whatsapp.py, services/payment/momo_orange.py) sont invisibles
# par defaut (root logger a WARNING) — hors ces stubs sont le seul moyen
# d'observer ce qui aurait ete envoye tant que les identifiants reels ne
# sont pas configures (§5.2).
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler()
    if get_settings().scheduler_enabled:
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Trakist API", version="0.1.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(businesses.router)
app.include_router(offers.router)
app.include_router(products.router)
app.include_router(channels.router)
app.include_router(ingestion.router)
app.include_router(signals.router)
app.include_router(live.router)
app.include_router(reports.router)
app.include_router(admin.router)
