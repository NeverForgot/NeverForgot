from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.schemas.admin import DashboardPiloteOut
from trakist.services.admin.dashboard import sante_connecteurs, taux_pertinence_par_cohorte

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardPiloteOut)
def get_dashboard_pilote(db: Session = Depends(get_db)) -> dict:
    """Tableau de bord pilote interne (§3.5) : taux de pertinence par pays et
    par cohorte (secteur), pour decider du passage a l'ouverture large
    (§2.2), et sante des connecteurs par pays."""
    return {
        "taux_pertinence": taux_pertinence_par_cohorte(db),
        "sante_connecteurs": sante_connecteurs(db),
    }
