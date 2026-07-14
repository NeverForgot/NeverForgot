"""Seed initial des profils pays et du glossaire d'argot (cahier des
charges §4, §5.5.3, §7).

/!\\ JEU DE DEPART, PAS UNE CURATION FINALE. Les expressions ci-dessous
s'appuient sur de l'argot ouest-africain francophone documente publiquement
(notamment le Nouchi ivoirien) mais n'ont pas ete validees par des locuteurs
natifs de chaque pays. Le §7 du cahier des charges identifie ce point comme
le risque numero 1 au lancement : "un glossaire trop pauvre au demarrage
produit des rapports peu pertinents" et exige une "curation initiale avec
des locuteurs natifs de chaque pays avant meme le premier pilote". Ne pas
lancer un pilote sur ce seul jeu de donnees sans validation native BJ/CI/SN
— c'est particulierement vrai pour le Benin, qui n'a aucune entree
specifique ici faute de source fiable.

Idempotent : peut etre relance sans dupliquer les entrees deja presentes.

Usage :
    python -m trakist.scripts.seed_glossary
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from trakist.db import SessionLocal, init_db
from trakist.models.market import Country, GlossaryCategorie, GlossaryEntry, GlossarySource

# Rails de paiement : Orange Money confirme en Cote d'Ivoire et au Senegal
# (§5.2). MTN MoMo suppose disponible dans les 3 pays mais a reverifier
# precisement pour le Benin avant toute integration reelle (§7).
COUNTRIES = [
    Country(code="BJ", langue_dominante="fr", rails_paiement_disponibles=["momo"]),
    Country(code="CI", langue_dominante="fr", rails_paiement_disponibles=["momo", "orange_money"]),
    Country(code="SN", langue_dominante="fr", rails_paiement_disponibles=["momo", "orange_money"]),
]

_Entry = tuple[str, str, str, GlossaryCategorie]

# Socle partage (country_code=None) : expressions communes a l'espace
# ouest-africain francophone urbain, liees a l'achat/la negociation.
SOCLE_PARTAGE: list[_Entry] = [
    ("chaud", "tres motive/interesse pour acheter", "j'suis chaud pour ca", GlossaryCategorie.INTENTION_ACHAT),
    ("deal", "d'accord, affaire conclue (emprunt anglais courant)", "ok deal, j'achete", GlossaryCategorie.NEGOCIATION),
    ("ça tape", "c'est bien, ca me plait", "ce modele ça tape", GlossaryCategorie.INTENTION_ACHAT),
    ("y'a moyen", "est-ce possible / peux-tu faire un geste sur le prix", "y'a moyen tu baisses un peu ?", GlossaryCategorie.NEGOCIATION),
    ("dispo", "disponible", "c'est dispo en quelle taille ?", GlossaryCategorie.QUESTION),
    ("combien ça fait", "quel est le prix", "tu le fais a combien ?", GlossaryCategorie.QUESTION),
    ("je le veux", "intention d'achat explicite", "je le veux, comment on fait ?", GlossaryCategorie.INTENTION_ACHAT),
    ("on gère", "c'est bon, on s'arrange / affaire en cours", "ok on gere, envoie ton numero", GlossaryCategorie.NEGOCIATION),
]

# Couche specifique par pays, ajoutee au-dessus du socle partage.
SPECIFIQUE_PAR_PAYS: dict[str, list[_Entry]] = {
    "CI": [
        ("wesh", "interpellation familiere (Nouchi)", "wesh, c'est combien ?", GlossaryCategorie.AUTRE),
        ("c'est comment", "comment ca se passe / quelles sont les modalites (Nouchi)", "c'est comment pour la livraison ?", GlossaryCategorie.QUESTION),
        ("gaou", "personne naive (Nouchi) — signal negatif/moqueur, pas une intention d'achat", "sois pas gaou, fais-moi un prix", GlossaryCategorie.AUTRE),
    ],
    "SN": [
        ("on est ensemble", "on est d'accord / affaire conclue (tres courant au Senegal)", "ok on est ensemble pour la robe", GlossaryCategorie.NEGOCIATION),
        ("waw", "oui / d'accord (interjection d'origine wolof)", "waw je prends deux", GlossaryCategorie.INTENTION_ACHAT),
        ("first", "vouloir etre servi en premier (emprunt anglais)", "je veux etre first sur celui-la", GlossaryCategorie.INTENTION_ACHAT),
    ],
    "BJ": [],
}


def seed(session: Session) -> None:
    for country in COUNTRIES:
        if session.get(Country, country.code) is None:
            session.add(country)
    session.flush()

    _seed_entries(session, SOCLE_PARTAGE, country_code=None)
    for code, entries in SPECIFIQUE_PAR_PAYS.items():
        _seed_entries(session, entries, country_code=code)

    session.commit()


def _seed_entries(session: Session, entries: list[_Entry], country_code: str | None) -> None:
    for expression, signification, exemple, categorie in entries:
        deja_present = (
            session.query(GlossaryEntry)
            .filter_by(expression=expression, country_code=country_code)
            .first()
        )
        if deja_present is not None:
            continue
        session.add(
            GlossaryEntry(
                country_code=country_code,
                expression=expression,
                signification=signification,
                exemple_usage=exemple,
                categorie=categorie,
                source=GlossarySource.CURATION_MANUELLE,
            )
        )


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        seed(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
