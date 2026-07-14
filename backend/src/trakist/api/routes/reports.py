import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.signal import Report
from trakist.schemas.report import ReportOut
from trakist.services.reporting.scheduler import ReportScheduler

router = APIRouter(tags=["reports"])


@router.post("/reports/generer", response_model=list[ReportOut])
def generer_rapports_dus(db: Session = Depends(get_db)) -> list[Report]:
    """A appeler par un ordonnanceur periodique (cron, Celery beat...) — pas
    d'ordonnanceur automatique dans ce squelette (§3.2, §3.3)."""
    return ReportScheduler(db).generer_rapports_dus()


@router.get("/businesses/{business_id}/reports", response_model=list[ReportOut])
def list_reports(business_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Report]:
    """Historique des rapports envoyes, consultable a la demande (§3.3)."""
    return (
        db.query(Report)
        .filter(Report.business_id == business_id)
        .order_by(Report.periode_fin.desc())
        .all()
    )
