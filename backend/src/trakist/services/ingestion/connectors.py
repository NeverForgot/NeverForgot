"""Connecteurs d'ingestion (cahier des charges §5.2). Chaque connecteur
expose fetch_new_messages() et renvoie des messages bruts a pousser dans la
file (voir queue.py). Les appels reels aux APIs externes necessitent des
identifiants qui ne sont pas encore configures a ce stade du squelette : a
implementer au moment du branchement de chaque canal, pays par pays.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RawMessage:
    channel_id: str
    auteur: str | None
    texte: str
    url_source: str | None
    horodatage: str


class BaseConnector(ABC):
    def __init__(self, channel_id: str, identifiant_externe: str) -> None:
        self.channel_id = channel_id
        self.identifiant_externe = identifiant_externe

    @abstractmethod
    def fetch_new_messages(self) -> list[RawMessage]:
        """Recupere les nouveaux messages depuis la derniere synchronisation."""


class FacebookWhatsAppGroupConnector(BaseConnector):
    """Groupes ou le bot a ete ajoute par l'entrepreneur (API Graph)."""

    def fetch_new_messages(self) -> list[RawMessage]:
        raise NotImplementedError(
            "Brancher l'API Graph Facebook/WhatsApp. Voir cahier des charges §5.2."
        )


class TikTokOwnAccountConnector(BaseConnector):
    """Compte TikTok createur propre de l'entrepreneur (outils createur / API officielle)."""

    def fetch_new_messages(self) -> list[RawMessage]:
        raise NotImplementedError(
            "Brancher l'API createur TikTok. Voir cahier des charges §5.2."
        )


class GoogleSearchConnector(BaseConnector):
    """Recherche Google (API de recherche) pour les mentions publiques."""

    def fetch_new_messages(self) -> list[RawMessage]:
        raise NotImplementedError(
            "Brancher l'API de recherche Google. Voir cahier des charges §5.2."
        )
