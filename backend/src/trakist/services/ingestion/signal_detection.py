"""Moteur de veille : transforme un message brut (connecteur) en Signal
persiste, via le service de classification (cahier des charges §3.2, §5.3).

C'est la piece qui relie l'ingestion (connectors.py, queue.py — pas encore
branches a de vraies API externes, §5.2) a la classification
(classification/factory.py) : sans elle, un message ingere ne devient
jamais un prospect detecte et rapportable.

Le message est classifie contre chaque Offer declaree par le Business, et
le Signal cree correspond a la meilleure correspondance (score_pertinence
le plus eleve). Sans Offer declaree, il n'y a rien a comparer : aucun
Signal n'est cree.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from trakist.models.business import Business, Offer
from trakist.models.signal import LangueDetectee, Signal, StatutSignal
from trakist.services.classification.classifier import Classifier, ClassificationResult
from trakist.services.classification.prompt import OfferContext
from trakist.services.ingestion.connectors import RawMessage

# Sous ce seuil de confiance linguistique, le signal est marque incertain
# plutot que classe silencieusement pertinent ou non pertinent (§5.5.4).
SEUIL_CONFIANCE_INCERTAIN = 0.5


class SignalDetectionService:
    def __init__(self, db: Session, classifier: Classifier) -> None:
        self._db = db
        self._classifier = classifier

    def traiter_message(self, message: RawMessage, business: Business) -> Signal | None:
        offers = self._db.query(Offer).filter(Offer.business_id == business.id).all()
        if not offers:
            return None

        meilleure_offer, meilleur_resultat = self._meilleure_correspondance(message, business, offers)

        statut = (
            StatutSignal.INCERTAIN
            if meilleur_resultat.score_confiance_linguistique < SEUIL_CONFIANCE_INCERTAIN
            else StatutSignal.NOUVEAU
        )

        signal = Signal(
            channel_id=uuid.UUID(str(message.channel_id)),
            business_id=business.id,
            offer_id=meilleure_offer.id,
            texte_source=message.texte,
            url_source=message.url_source,
            auteur=message.auteur,
            langue_detectee=LangueDetectee(meilleur_resultat.langue_detectee.value),
            expressions_argot_matchees=meilleur_resultat.expressions_argot_matchees,
            score_pertinence=meilleur_resultat.score_pertinence,
            score_confiance_linguistique=meilleur_resultat.score_confiance_linguistique,
            statut=statut,
        )
        self._db.add(signal)
        self._db.commit()
        self._db.refresh(signal)
        return signal

    def _meilleure_correspondance(
        self, message: RawMessage, business: Business, offers: list[Offer]
    ) -> tuple[Offer, ClassificationResult]:
        """offers est garanti non vide par l'appelant."""
        resultats = [
            (
                offer,
                self._classifier.classify(
                    message.texte,
                    OfferContext(
                        libelle=offer.libelle,
                        mots_cles=offer.mots_cles,
                        secteur=business.secteur,
                        zone_geo_cible=offer.zone_geo_cible,
                    ),
                    business.country_code,
                ),
            )
            for offer in offers
        ]
        return max(resultats, key=lambda paire: paire[1].score_pertinence)
