from sqlalchemy.orm import Session

from trakist.models.business import Business, Channel
from trakist.models.signal import LangueDetectee, Signal, StatutSignal
from trakist.services.notification.whatsapp import WhatsAppClient
from trakist.services.reporting.scheduler import ReportScheduler


class _FakeWhatsAppClient(WhatsAppClient):
    def __init__(self) -> None:
        super().__init__()
        self.appels: list[tuple[str, list]] = []

    def send_report(self, destinataire: str, lignes: list) -> None:
        self.appels.append((destinataire, lignes))


def _creer_signal(
    db_session: Session,
    business: Business,
    channel: Channel,
    score: float = 0.8,
    statut: StatutSignal = StatutSignal.NOUVEAU,
    texte: str = "Je suis chaud pour la robe",
) -> Signal:
    signal = Signal(
        channel_id=channel.id,
        business_id=business.id,
        texte_source=texte,
        langue_detectee=LangueDetectee.FR,
        score_pertinence=score,
        score_confiance_linguistique=0.9,
        statut=statut,
    )
    db_session.add(signal)
    db_session.commit()
    db_session.refresh(signal)
    return signal


def test_genere_et_envoie_le_rapport_si_signaux_pertinents(
    db_session: Session, business: Business, channel: Channel
) -> None:
    _creer_signal(db_session, business, channel, score=0.8)
    fake_whatsapp = _FakeWhatsAppClient()
    scheduler = ReportScheduler(db_session, whatsapp_client=fake_whatsapp)

    rapports = scheduler.generer_rapports_dus()

    assert len(rapports) == 1
    assert rapports[0].envoye_at is not None
    assert len(fake_whatsapp.appels) == 1
    destinataire, lignes = fake_whatsapp.appels[0]
    assert destinataire == business.numero_whatsapp
    assert len(lignes) == 1
    assert lignes[0].score_pertinence == 0.8


def test_pas_de_rapport_sans_signal(db_session: Session, business: Business) -> None:
    scheduler = ReportScheduler(db_session, whatsapp_client=_FakeWhatsAppClient())
    assert scheduler.generer_rapports_dus() == []


def test_signaux_sous_le_seuil_de_pertinence_exclus(
    db_session: Session, business: Business, channel: Channel
) -> None:
    business.seuil_pertinence = 0.6
    db_session.commit()
    _creer_signal(db_session, business, channel, score=0.3)

    scheduler = ReportScheduler(db_session, whatsapp_client=_FakeWhatsAppClient())
    assert scheduler.generer_rapports_dus() == []


def test_signaux_deja_juges_non_repris(
    db_session: Session, business: Business, channel: Channel
) -> None:
    _creer_signal(db_session, business, channel, score=0.9, statut=StatutSignal.JUGE_PERTINENT)

    scheduler = ReportScheduler(db_session, whatsapp_client=_FakeWhatsAppClient())
    assert scheduler.generer_rapports_dus() == []


def test_pas_de_second_rapport_avant_la_prochaine_echeance(
    db_session: Session, business: Business, channel: Channel
) -> None:
    _creer_signal(db_session, business, channel, score=0.8)
    scheduler = ReportScheduler(db_session, whatsapp_client=_FakeWhatsAppClient())
    premier = scheduler.generer_rapports_dus()
    assert len(premier) == 1

    _creer_signal(db_session, business, channel, score=0.9, texte="Deuxieme message")
    second = scheduler.generer_rapports_dus()

    assert second == []  # rapport quotidien pas encore du


def test_marque_les_signaux_envoyes_au_rapport(
    db_session: Session, business: Business, channel: Channel
) -> None:
    signal = _creer_signal(db_session, business, channel, score=0.8)
    scheduler = ReportScheduler(db_session, whatsapp_client=_FakeWhatsAppClient())
    rapports = scheduler.generer_rapports_dus()

    db_session.refresh(signal)
    assert signal.statut == StatutSignal.ENVOYE_AU_RAPPORT
    assert signal.report_id == rapports[0].id
