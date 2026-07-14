"""Tableau de bord pilote interne (cahier des charges §3.5) : suivi du taux
de pertinence des signaux par pays et par cohorte, pour decider du passage
a l'ouverture large (§2.2).

Une « cohorte » pilote correspond ici au couple (pays, secteur) : le
cahier des charges ne definit pas d'entite Cohort dediee, et les pilotes
sont recrutes par secteur au sein de chaque pays (§2.2) — ce qui correspond
deja a Business.secteur, sans dupliquer l'information dans une nouvelle
table.

Le suivi des couts d'API par entrepreneur (§3.5) n'est pas couvert ici :
aucune instrumentation de cout n'existe encore dans l'architecture
(tokens LLM, messages WhatsApp envoyes...) — a construire separement une
fois les volumes reels observes en pilote.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from trakist.models.business import Business, Channel, ChannelType, StatutConnexion
from trakist.models.signal import Signal, StatutSignal

# Seuil indicatif du §2.2 : « Ouverture large par pays uniquement une fois le
# taux de pertinence des rapports valide sur la cohorte pilote (seuil a
# definir, ex. >70% de signaux juges pertinents par les pilotes). »
SEUIL_OUVERTURE_LARGE = 0.70


@dataclass
class TauxPertinenceParCohorte:
    country_code: str
    secteur: str
    nombre_signaux_juges: int
    nombre_pertinents: int
    taux_pertinence: float | None
    seuil_ouverture_large_atteint: bool


@dataclass
class SanteConnecteurs:
    country_code: str
    type: ChannelType
    statut_connexion: StatutConnexion
    nombre: int


def taux_pertinence_par_cohorte(db: Session) -> list[TauxPertinenceParCohorte]:
    """Signaux juges = jugé_pertinent + jugé_non_pertinent (feedback humain
    explicite, §3.3). Les signaux nouveau/envoyé_au_rapport/incertain ne
    comptent pas encore comme un jugement."""
    juges_expr = func.sum(
        case(
            (Signal.statut.in_([StatutSignal.JUGE_PERTINENT, StatutSignal.JUGE_NON_PERTINENT]), 1),
            else_=0,
        )
    )
    pertinents_expr = func.sum(case((Signal.statut == StatutSignal.JUGE_PERTINENT, 1), else_=0))

    stmt = (
        select(Business.country_code, Business.secteur, juges_expr, pertinents_expr)
        .join(Signal, Signal.business_id == Business.id)
        .group_by(Business.country_code, Business.secteur)
        .order_by(Business.country_code, Business.secteur)
    )

    resultats: list[TauxPertinenceParCohorte] = []
    for country_code, secteur, nombre_juges, nombre_pertinents in db.execute(stmt):
        nombre_juges = nombre_juges or 0
        nombre_pertinents = nombre_pertinents or 0
        taux = (nombre_pertinents / nombre_juges) if nombre_juges else None
        resultats.append(
            TauxPertinenceParCohorte(
                country_code=country_code,
                secteur=secteur,
                nombre_signaux_juges=nombre_juges,
                nombre_pertinents=nombre_pertinents,
                taux_pertinence=taux,
                seuil_ouverture_large_atteint=taux is not None and taux >= SEUIL_OUVERTURE_LARGE,
            )
        )
    return resultats


def sante_connecteurs(db: Session) -> list[SanteConnecteurs]:
    stmt = (
        select(Business.country_code, Channel.type, Channel.statut_connexion, func.count(Channel.id))
        .join(Channel, Channel.business_id == Business.id)
        .group_by(Business.country_code, Channel.type, Channel.statut_connexion)
        .order_by(Business.country_code, Channel.type)
    )
    return [
        SanteConnecteurs(country_code=cc, type=t, statut_connexion=s, nombre=n)
        for cc, t, s, n in db.execute(stmt)
    ]
