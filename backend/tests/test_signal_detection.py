from sqlalchemy.orm import Session

from trakist.models.business import Business, Channel, Offer
from trakist.models.signal import StatutSignal
from trakist.services.classification.classifier import ClassificationResult
from trakist.services.ingestion.connectors import RawMessage
from trakist.services.ingestion.signal_detection import SignalDetectionService
from trakist.services.market_context.language import Langue


class _FakeClassifier:
    def __init__(self, scores: dict[str, float], confiance: float = 0.9) -> None:
        self._scores = scores  # cle = offer.libelle
        self._confiance = confiance

    def classify(self, texte_message, offer, country_code) -> ClassificationResult:
        return ClassificationResult(
            langue_detectee=Langue.FR,
            expressions_argot_matchees=[],
            score_pertinence=self._scores.get(offer.libelle, 0.0),
            score_confiance_linguistique=self._confiance,
            prompt_utilise="prompt",
        )


def _offer(db_session: Session, business: Business, libelle: str) -> Offer:
    offer = Offer(business_id=business.id, libelle=libelle, mots_cles=[], zone_geo_cible=None)
    db_session.add(offer)
    db_session.commit()
    db_session.refresh(offer)
    return offer


def _message(channel: Channel, texte: str = "texte") -> RawMessage:
    return RawMessage(
        channel_id=str(channel.id),
        auteur="Fatou",
        texte=texte,
        url_source=None,
        horodatage="2026-01-01T00:00:00",
    )


def test_traiter_message_choisit_la_meilleure_offer(
    db_session: Session, business: Business, channel: Channel
) -> None:
    offer_robe = _offer(db_session, business, "Robe wax")
    _offer(db_session, business, "Sac a main")
    classifier = _FakeClassifier({"Robe wax": 0.9, "Sac a main": 0.2})
    service = SignalDetectionService(db_session, classifier)

    signal = service.traiter_message(_message(channel, "Je veux la robe"), business)

    assert signal is not None
    assert signal.offer_id == offer_robe.id
    assert signal.score_pertinence == 0.9
    assert signal.statut == StatutSignal.NOUVEAU


def test_traiter_message_confiance_basse_marque_incertain(
    db_session: Session, business: Business, channel: Channel
) -> None:
    _offer(db_session, business, "Robe wax")
    classifier = _FakeClassifier({"Robe wax": 0.9}, confiance=0.3)
    service = SignalDetectionService(db_session, classifier)

    signal = service.traiter_message(_message(channel), business)

    assert signal is not None
    assert signal.statut == StatutSignal.INCERTAIN


def test_traiter_message_sans_offer_renvoie_none(
    db_session: Session, business: Business, channel: Channel
) -> None:
    classifier = _FakeClassifier({})
    service = SignalDetectionService(db_session, classifier)

    assert service.traiter_message(_message(channel), business) is None
