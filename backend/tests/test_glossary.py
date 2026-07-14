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


def test_match_expressions_ignore_les_sous_chaines_a_l_interieur_d_un_mot() -> None:
    """'deal' ne doit pas matcher a l'interieur de 'ideal', ni 'non' a
    l'interieur de 'sinon' — frequent en francais avec des expressions
    courtes d'une syllabe."""
    from trakist.services.market_context.glossary import GlossaryEntryData

    service = GlossaryService(
        [
            GlossaryEntryData("deal", "affaire conclue", "negociation", country_code=None),
            GlossaryEntryData("non", "refus", "autre", country_code=None),
        ]
    )

    matches = service.match_expressions("C'est l'ideal pour moi, sinon je repasserai", "CI")

    assert matches == []


def test_match_entries_conserve_la_categorie(glossary_service: GlossaryService) -> None:
    entries = glossary_service.match_entries("wesh, ca va ?", "CI")
    assert [e.categorie for e in entries] == ["autre"]
