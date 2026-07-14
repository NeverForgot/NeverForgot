# Trakist — backend

Squelette de service backend pour Trakist (veille commerciale + réconciliation
des ventes live — Bénin, Côte d'Ivoire, Sénégal). Voir `../docs/cahier-des-charges.md`
pour le cahier des charges complet.

## Structure

- `src/trakist/models` — entités du §4 (Country, GlossaryEntry, Business, Offer,
  Channel, Signal, Report, LiveSession, LiveComment, Reservation, Transaction).
- `src/trakist/services/market_context` — détection de langue/code-switching et
  service de glossaire par pays (§5.5).
- `src/trakist/services/classification` — construction du prompt et classification.
  `factory.get_classifier()` bascule automatiquement vers `AnthropicClassifier`
  (sortie structurée via `client.messages.parse`) si `ANTHROPIC_API_KEY` est
  configurée, sinon reste sur `RuleBasedFallbackClassifier`.
- `src/trakist/services/ingestion` — connecteurs (Facebook/WhatsApp, TikTok,
  recherche Google) et file de messages Redis Streams.
- `src/trakist/services/reconciliation` — machine à états pure (`state_machine.py`)
  et service persistant (`live_service.py`) du module de vente live (§3.4, §5.4).
- `src/trakist/services/payment` — client Request-to-Pay MTN MoMo / Orange Money
  (stub en attendant les identifiants réels par pays, §5.2).
- `src/trakist/services/notification` — livraison des rapports par WhatsApp (§3.3).
- `src/trakist/services/reporting` — `ReportScheduler` : regroupe les `Signal`
  dus par `Business` (quotidien/hebdo, seuil de pertinence) et déclenche
  l'envoi WhatsApp (§3.2, §3.3).
- `src/trakist/services/admin` — tableau de bord pilote interne (§3.5) : taux
  de pertinence par pays/cohorte (§2.2) et santé des connecteurs.
- `src/trakist/api` — API FastAPI : santé, entrepreneurs, signaux + boucle de
  correction humaine, flux live (`/live-sessions`, `/live-sessions/{id}/comments`,
  `/webhooks/payments/momo`, `/live-sessions/{id}/journal`, `/reservations/{id}/expirer`),
  rapports (`POST /reports/generer`, `GET /businesses/{id}/reports`) et
  administration (`GET /admin/dashboard`).

## Démarrage local

```bash
cp .env.example .env
docker compose up -d          # Postgres + Redis
pip install -e ".[dev]"
alembic upgrade head                        # applique le schéma (§4)
python -m trakist.scripts.seed_glossary     # seed pays + glossaire de départ (§5.5.3)
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
- Le classifieur LLM (`AnthropicClassifier`) est branché et testé (sortie
  structurée validée par schéma, repli en statut « incertain » — jamais une
  exception ni une supposition silencieuse — sur erreur API, timeout ou refus,
  §5.5.4). Modèle par défaut : Haiku 4.5 (`classification_model` dans les
  settings), à ajuster selon le taux de pertinence mesuré en cohorte pilote
  (§2.2). Sans `ANTHROPIC_API_KEY` configurée, le squelette reste sur le
  fallback par règles (`RuleBasedFallbackClassifier`) — pratique pour les
  tests et le développement local sans clé API.
- Migrations Alembic en place (`alembic/`) : `alembic upgrade head` /
  `alembic downgrade base` testés de bout en bout contre un vrai Postgres,
  y compris la suppression explicite des types ENUM natifs au downgrade
  (Alembic ne le fait pas automatiquement — sinon un downgrade puis upgrade
  échoue avec « type already exists »). `alembic revision --autogenerate`
  pour les évolutions futures du schéma.
- `python -m trakist.scripts.seed_glossary` seed les 3 `Country` (BJ/CI/SN)
  et un glossaire de départ (socle partagé + couche par pays, §5.5.2-3),
  idempotent. **Ceci est un jeu de données de départ, pas une curation
  finale** : les expressions n'ont pas été validées par des locuteurs
  natifs — le §7 du cahier des charges identifie ça comme le risque n°1
  avant tout pilote, particulièrement pour le Bénin qui n'a aucune entrée
  spécifique ici faute de source fiable.
- Le flux live -> réservation -> paiement -> confirmation/expiration est
  branché de bout en bout (service + API), testé avec 19 tests dont un test
  d'intégration API complet (`tests/test_live_api.py`). L'expiration n'a pas
  encore d'ordonnanceur périodique : `POST /reservations/{id}/expirer` doit
  être appelé par un worker externe (cron, Celery beat, etc.) une fois la
  fenêtre dépassée — non modélisé dans ce squelette.
- Le montant de la transaction est un placeholder (`0.0`) : la réservation
  n'est pas encore reliée à un catalogue produit/prix, hors périmètre du §4
  actuel.
- `ReportScheduler` regroupe les `Signal` au statut `nouveau` au-dessus du
  seuil `Business.seuil_pertinence`, sur une fenêtre glissante (fin du
  dernier rapport → maintenant, plutôt qu'un alignement calendaire par
  fuseau horaire — `Business.fuseau_horaire` n'est pas encore exploité ici).
  Aucun rapport vide n'est envoyé. Pas d'ordonnanceur automatique dans ce
  squelette : `POST /reports/generer` doit être appelé par un worker externe
  périodique (cron, Celery beat...), comme pour l'expiration des réservations
  live.
- `GET /admin/dashboard` (§3.5) : taux de pertinence par couple (pays,
  secteur) — une « cohorte » pilote n'a pas d'entité dédiée dans le modèle,
  le secteur en fait office (§2.2) — avec seuil d'alerte à 70% (§2.2), et
  santé des connecteurs par pays/type/statut. Le suivi des coûts d'API par
  entrepreneur (§3.5) n'est pas couvert : aucune instrumentation de coût
  n'existe encore dans l'architecture.
