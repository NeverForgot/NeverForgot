import logging

from fastapi import FastAPI

from trakist.api.routes import (
    admin,
    businesses,
    channels,
    health,
    ingestion,
    live,
    offers,
    reports,
    signals,
)

# Sans ceci, les logger.info(...) des stubs WhatsApp/paiement (services/
# notification/whatsapp.py, services/payment/momo_orange.py) sont invisibles
# par defaut (root logger a WARNING) — hors ces stubs sont le seul moyen
# d'observer ce qui aurait ete envoye tant que les identifiants reels ne
# sont pas configures (§5.2).
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Trakist API", version="0.1.0")

app.include_router(health.router)
app.include_router(businesses.router)
app.include_router(offers.router)
app.include_router(channels.router)
app.include_router(ingestion.router)
app.include_router(signals.router)
app.include_router(live.router)
app.include_router(reports.router)
app.include_router(admin.router)
