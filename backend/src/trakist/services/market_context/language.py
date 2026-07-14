"""Detection de langue et de code-switching FR/EN (cahier des charges §5.5.1).

Implementation de depart : heuristique par listes de marqueurs lexicaux. A
completer par un modele de langue ou un appel LLM une fois les donnees des
cohortes pilotes disponibles pour calibrer les seuils par pays.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Langue(str, Enum):
    FR = "fr"
    EN = "en"
    MIXTE = "mixte"


_EN_MARKERS = {
    "let's", "let", "go", "please", "ok", "okay", "yes", "price",
    "order", "buy", "send", "deal", "available", "the", "for", "with",
}

_FR_MARKERS = {
    "je", "suis", "pour", "combien", "prix", "disponible", "commande",
    "acheter", "envoyer", "svp", "merci", "bonjour", "oui", "non", "dispo",
}

_TOKEN_RE = re.compile(r"[a-zàâäéèêëïîôöùûüç']+", re.IGNORECASE)


@dataclass
class LanguageDetectionResult:
    langue: Langue
    ratio_marqueurs_anglais: float
    tokens_anglais_detectes: list[str]


class LanguageDetector:
    """Detecteur de langue + code-switching, base sur des marqueurs lexicaux."""

    def __init__(
        self,
        en_markers: set[str] | None = None,
        fr_markers: set[str] | None = None,
        seuil_mixte_bas: float = 0.15,
        seuil_mixte_haut: float = 0.6,
    ) -> None:
        self._en_markers = en_markers or _EN_MARKERS
        self._fr_markers = fr_markers or _FR_MARKERS
        self._seuil_mixte_bas = seuil_mixte_bas
        self._seuil_mixte_haut = seuil_mixte_haut

    def detect(self, texte: str) -> LanguageDetectionResult:
        tokens = [t.lower() for t in _TOKEN_RE.findall(texte)]
        if not tokens:
            return LanguageDetectionResult(Langue.FR, 0.0, [])

        tokens_en = [t for t in tokens if t in self._en_markers]
        tokens_fr = [t for t in tokens if t in self._fr_markers]
        marqueurs_connus = len(tokens_en) + len(tokens_fr)

        if marqueurs_connus == 0:
            # Aucun marqueur reconnu : on suppose francais par defaut (langue
            # dominante des 3 pays de lancement), a affiner en aval par le
            # score de confiance du service de classification.
            return LanguageDetectionResult(Langue.FR, 0.0, [])

        ratio_en = len(tokens_en) / marqueurs_connus

        if ratio_en >= self._seuil_mixte_haut:
            langue = Langue.EN
        elif ratio_en >= self._seuil_mixte_bas:
            langue = Langue.MIXTE
        else:
            langue = Langue.FR

        return LanguageDetectionResult(langue, ratio_en, tokens_en)
