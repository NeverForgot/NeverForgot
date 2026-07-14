import uuid

from pydantic import BaseModel, ConfigDict

from trakist.models.business import ChannelType, StatutConnexion


class ChannelCreate(BaseModel):
    type: ChannelType
    identifiant_externe: str
    # La creation via l'API represente l'etape d'onboarding "bot ajoute /
    # compte lie" (§3.1) : on considere le canal connecte par defaut, sauf
    # indication contraire explicite du client.
    statut_connexion: StatutConnexion = StatutConnexion.CONNECTE


class ChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    type: ChannelType
    identifiant_externe: str
    statut_connexion: StatutConnexion
