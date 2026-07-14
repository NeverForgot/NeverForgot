from trakist.services.market_context.glossary import GlossaryService


def test_for_country_fusionne_socle_partage_et_specifique(glossary_service: GlossaryService) -> None:
    entries_ci = glossary_service.for_country("CI")
    expressions = {e.expression for e in entries_ci}
    assert "chaud" in expressions  # socle partage
    assert "wesh" in expressions  # specifique CI
    assert "first" not in expressions  # specifique SN, absent pour CI


def test_match_expressions_dans_un_texte(glossary_service: GlossaryService) -> None:
    matches = glossary_service.match_expressions("Je suis chaud pour ca, wesh tu es dispo ?", "CI")
    assert set(matches) == {"chaud", "wesh"}
