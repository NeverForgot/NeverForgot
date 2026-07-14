import uuid

import pytest

from trakist.services.notification.feedback_parser import FeedbackParseError, parse_feedback_message


def test_parse_oui() -> None:
    signal_id = uuid.uuid4()
    resultat = parse_feedback_message(f"OUI (ref {signal_id})")
    assert resultat.signal_id == signal_id
    assert resultat.pertinent is True


def test_parse_non() -> None:
    signal_id = uuid.uuid4()
    resultat = parse_feedback_message(f"non (ref {signal_id})")
    assert resultat.signal_id == signal_id
    assert resultat.pertinent is False


def test_parse_insensible_a_la_casse_et_aux_espaces() -> None:
    signal_id = uuid.uuid4()
    resultat = parse_feedback_message(f"  Oui   (ref {signal_id}) merci")
    assert resultat.pertinent is True


def test_parse_sans_reference_leve_une_erreur() -> None:
    with pytest.raises(FeedbackParseError):
        parse_feedback_message("oui")


def test_parse_mot_non_reconnu_leve_une_erreur() -> None:
    signal_id = uuid.uuid4()
    with pytest.raises(FeedbackParseError):
        parse_feedback_message(f"peut-etre (ref {signal_id})")
