from pydantic import BaseModel, ConfigDict

from trakist.models.business import ChannelType, StatutConnexion


class TauxPertinenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    country_code: str
    secteur: str
    nombre_signaux_juges: int
    nombre_pertinents: int
    taux_pertinence: float | None
    seuil_ouverture_large_atteint: bool


class SanteConnecteursOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    country_code: str
    type: ChannelType
    statut_connexion: StatutConnexion
    nombre: int


class DashboardPiloteOut(BaseModel):
    taux_pertinence: list[TauxPertinenceOut]
    sante_connecteurs: list[SanteConnecteursOut]
