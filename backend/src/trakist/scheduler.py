"""Ordonnanceur interne (§3.2, §3.3, §3.4) : jusqu'ici `POST /reports/generer`
et `POST /reservations/{id}/expirer` devaient etre declenches par un worker
externe (cron, Celery beat...). Ce module les declenche automatiquement dans
le process API lui-meme via APScheduler — suffisant pour un pilote
mono-instance ; a remplacer par un ordonnanceur externe partage si le service
passe un jour multi-instance (deux instances avec ce scheduler activé
declencheraient chacune les memes jobs en double).
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from trakist.config import get_settings
from trakist.db import SessionLocal
from trakist.services.reconciliation.live_service import LiveReconciliationService
from trakist.services.reporting.scheduler import ReportScheduler

logger = logging.getLogger(__name__)


def _job_generer_rapports() -> None:
    db = SessionLocal()
    try:
        rapports = ReportScheduler(db).generer_rapports_dus()
        if rapports:
            logger.info("Ordonnanceur : %d rapport(s) genere(s) et envoye(s).", len(rapports))
    except Exception:
        logger.exception("Ordonnanceur : echec de la generation des rapports.")
        db.rollback()
    finally:
        db.close()


def _job_expirer_reservations() -> None:
    db = SessionLocal()
    try:
        expirees = LiveReconciliationService(db).expirer_toutes_dues()
        if expirees:
            logger.info("Ordonnanceur : %d reservation(s) expiree(s).", len(expirees))
    except Exception:
        logger.exception("Ordonnanceur : echec de l'expiration des reservations.")
        db.rollback()
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _job_generer_rapports,
        "interval",
        minutes=settings.scheduler_intervalle_rapports_minutes,
        id="generer_rapports",
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        _job_expirer_reservations,
        "interval",
        minutes=settings.scheduler_intervalle_reservations_minutes,
        id="expirer_reservations",
        coalesce=True,
        max_instances=1,
    )
    return scheduler
