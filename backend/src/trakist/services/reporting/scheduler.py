"""Ordonnanceur de rapports WhatsApp (cahier des charges §3.2, §3.3).

Regroupe les Signal du jour/semaine par Business et declenche l'envoi via
WhatsAppClient, au rythme declare par l'entrepreneur a l'onboarding
(Business.frequence_rapport), en filtrant sur le seuil de pertinence
configurable par entrepreneur (Business.seuil_pertinence) pour eviter la
fatigue du rapport.

Fenetre glissante plutot que calendaire : la periode d'un rapport va de la
fin du rapport precedent (ou de la creation du Business, au premier envoi)
jusqu'a l'instant de generation. Ca evite la complexite des fuseaux horaires
par pays/business (Business.fuseau_horaire n'est pas encore exploite ici,
seul le rythme quotidien/hebdomadaire l'est) au prix d'un alignement moins
strict sur le jour calendaire — a affiner si le pilote montre que ca compte.
Aucun rapport vide n'est envoye : sans signal a rapporter, la generation est
simplement sautee pour ce Business.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from trakist.models.business import Business, Channel, ChannelType, FrequenceRapport
from trakist.models.signal import Report, Signal, StatutSignal
from trakist.services.notification.whatsapp import ReportLine, WhatsAppClient

_LABEL_CANAL = {
    ChannelType.FACEBOOK_GROUP: "Facebook",
    ChannelType.WHATSAPP_GROUP: "WhatsApp",
    ChannelType.TIKTOK_OWN: "TikTok",
    ChannelType.GOOGLE_SEARCH: "Recherche Google",
}

SEUIL_ACTION_PRIORITAIRE = 0.7


class ReportScheduler:
    def __init__(self, db: Session, whatsapp_client: WhatsAppClient | None = None) -> None:
        self._db = db
        self._whatsapp = whatsapp_client or WhatsAppClient()

    def generer_rapports_dus(self, now: datetime | None = None) -> list[Report]:
        """A appeler par un ordonnanceur periodique (cron, Celery beat...).

        Parcourt tous les Business et genere/envoie un rapport pour ceux qui
        sont dus et ont au moins un signal a rapporter.
        """
        now = now or datetime.utcnow()
        rapports_crees: list[Report] = []
        for business in self._db.execute(select(Business)).scalars():
            rapport = self._generer_si_du(business, now)
            if rapport is not None:
                rapports_crees.append(rapport)
        return rapports_crees

    def _generer_si_du(self, business: Business, now: datetime) -> Report | None:
        dernier_rapport = self._dernier_rapport_envoye(business.id)
        if not self._est_du(business, dernier_rapport, now):
            return None

        periode_debut = dernier_rapport.periode_fin if dernier_rapport else business.created_at
        signaux = self._signaux_a_rapporter(business, periode_debut, now)
        if not signaux:
            return None

        report = Report(business_id=business.id, periode_debut=periode_debut, periode_fin=now)
        self._db.add(report)
        self._db.flush()

        lignes = [self._construire_ligne(signal) for signal in signaux]
        for signal in signaux:
            signal.report_id = report.id
            signal.statut = StatutSignal.ENVOYE_AU_RAPPORT

        self._whatsapp.send_report(business.numero_whatsapp, lignes)
        report.envoye_at = now

        self._db.commit()
        self._db.refresh(report)
        return report

    def _dernier_rapport_envoye(self, business_id: uuid.UUID) -> Report | None:
        stmt = (
            select(Report)
            .where(Report.business_id == business_id, Report.envoye_at.is_not(None))
            .order_by(Report.envoye_at.desc())
        )
        return self._db.execute(stmt).scalars().first()

    @staticmethod
    def _est_du(business: Business, dernier_rapport: Report | None, now: datetime) -> bool:
        if dernier_rapport is None:
            return True
        delta = now - dernier_rapport.envoye_at
        seuil = (
            timedelta(days=1)
            if business.frequence_rapport == FrequenceRapport.DAILY
            else timedelta(days=7)
        )
        return delta >= seuil

    def _signaux_a_rapporter(
        self, business: Business, periode_debut: datetime, periode_fin: datetime
    ) -> list[Signal]:
        stmt = (
            select(Signal)
            .where(
                Signal.business_id == business.id,
                Signal.statut == StatutSignal.NOUVEAU,
                Signal.score_pertinence >= business.seuil_pertinence,
                Signal.date_detection >= periode_debut,
                Signal.date_detection <= periode_fin,
            )
            .order_by(Signal.score_pertinence.desc())
        )
        return list(self._db.execute(stmt).scalars())

    def _construire_ligne(self, signal: Signal) -> ReportLine:
        channel = self._db.get(Channel, signal.channel_id)
        source = _LABEL_CANAL.get(channel.type, "Autre") if channel else "Autre"
        action = (
            "Contacter en priorite"
            if signal.score_pertinence >= SEUIL_ACTION_PRIORITAIRE
            else "Evaluer et repondre"
        )
        return ReportLine(
            source=source,
            extrait=signal.texte_source,
            url=signal.url_source,
            score_pertinence=signal.score_pertinence,
            action_suggeree=action,
        )
