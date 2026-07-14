# Trakist — backend

Squelette de service backend pour Trakist (veille commerciale + réconciliation
des ventes live — Bénin, Côte d'Ivoire, Sénégal). Voir `../docs/cahier-des-charges.md`
pour le cahier des charges complet.

## Structure

- `src/trakist/models` — entités du §4 (Country, GlossaryEntry, Business, Offer,
  Channel, Signal, Report, LiveSession, LiveComment, Reservation, Transaction).
- `src/trakist/services/market_context` — détection de langue/code-switching et
  service de glossaire par pays (§5.5).
- `src/trakist/services/classification` — construction du prompt et classification
  (fallback par règles en attendant le branchement d'un LLM).
- `src/trakist/services/ingestion` — connecteurs (Facebook/WhatsApp, TikTok,
  recherche Google) et file de messages Redis Streams.
- `src/trakist/services/reconciliation` — machine à états du module de vente live
  (§3.4, §5.4).
- `src/trakist/services/notification` — livraison des rapports par WhatsApp (§3.3).
- `src/trakist/api` — API FastAPI (santé, entrepreneurs, signaux + boucle de
  correction humaine).

## Démarrage local

```bash
cp .env.example .env
docker compose up -d          # Postgres + Redis
pip install -e ".[dev]"
python -c "from trakist.db import init_db; init_db()"   # crée les tables (dev uniquement)
uvicorn trakist.api.main:app --reload
```

## Tests

```bash
pytest
```

## État du squelette

- Les connecteurs Facebook/WhatsApp, TikTok et Google Search sont définis mais
  non branchés (`NotImplementedError`) : ils nécessitent des identifiants
  d'API réels, à configurer canal par canal (§5.2).
- Le classifieur par défaut est une heuristique par mots-clés/glossaire, pas un
  appel LLM — suffisant pour les tests et pour valider le flux de bout en bout,
  à remplacer par un `Classifier` branché sur un modèle de langage pour la
  qualité de classification cible.
- Pas encore de migrations Alembic : `init_db()` crée les tables directement
  depuis les modèles SQLAlchemy pour le développement local.
