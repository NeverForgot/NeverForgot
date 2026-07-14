from trakist.services.market_context.language import Langue, LanguageDetector


def test_detect_francais_pur() -> None:
    detector = LanguageDetector()
    result = detector.detect("Bonjour, je suis interesse, combien pour deux pieces ?")
    assert result.langue == Langue.FR


def test_detect_code_switching() -> None:
    detector = LanguageDetector()
    result = detector.detect("Je suis chaud pour ca, let's go pour la commande")
    assert result.langue == Langue.MIXTE


def test_detect_anglais_dominant() -> None:
    detector = LanguageDetector()
    result = detector.detect("Let's go, please send order, for the price")
    assert result.langue == Langue.EN


def test_detect_texte_vide() -> None:
    detector = LanguageDetector()
    result = detector.detect("")
    assert result.langue == Langue.FR
    assert result.ratio_marqueurs_anglais == 0.0
