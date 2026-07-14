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
  recherche Google), file de messages Redis Streams, et `SignalDetectionService`
  (§3.2) : transforme un message brut en `Signal` classifié contre chaque
  `Offer` du `Business`, en gardant la meilleure correspondance.
- `src/trakist/services/reconciliation` — machine à états pure (`state_machine.py`)
  et service persistant (`live_service.py`) du module de vente live (§3.4, §5.4).
- `src/trakist/services/payment` — client Request-to-Pay MTN MoMo / Orange Money
  (stub en attendant les identifiants réels par pays, §5.2).
- `src/trakist/services/notification` — livraison des rapports par WhatsApp
  (§3.3) et `feedback_parser.py` : parse la réponse OUI/NON d'un
  entrepreneur au bouton de retour rapide, pour alimenter la boucle de
  correction humaine (§5.5.3).
- `src/trakist/services/reporting` — `ReportScheduler` : regroupe les `Signal`
  dus par `Business` (quotidien/hebdo, seuil de pertinence) et déclenche
  l'envoi WhatsApp (§3.2, §3.3).
- `src/trakist/services/admin` — tableau de bord pilote interne (§3.5) : taux
  de pertinence par pays/cohorte (§2.2) et santé des connecteurs.
- `src/trakist/api` — API FastAPI : onboarding (`/businesses`,
  `/businesses/{id}/offers`, `/businesses/{id}/channels`, §3.1), ingestion
  (`POST /channels/{id}/messages`, §3.2), signaux + boucle de correction
  humaine (`POST /signals/{id}/feedback`, `POST /webhooks/whatsapp/feedback`),
  flux live (`/live-sessions`, `/live-sessions/{id}/comments`,
  `/webhooks/payments/momo`, `/live-sessions/{id}/journal`,
  `/reservations/{id}/expirer`), catalogue produit (`/businesses/{id}/products`,
  §3.4), rapports (`POST /reports/generer`, `GET /businesses/{id}/reports`)
  et administration (`GET /admin/dashboard`).
- `src/trakist/scheduler.py` — ordonnanceur interne (APScheduler) : déclenche
  automatiquement la génération des rapports dus et l'expiration des
  réservations live, câblé au cycle de vie de l'app dans `api/main.py`.

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
  d'API réels, à configurer canal par canal (§5.2). En attendant,
  `POST /channels/{id}/messages` permet d'injecter un message manuellement
  et de vérifier le moteur de veille de bout en bout (langue → glossaire →
  classification → `Signal`), sans dépendre des connecteurs réels.
- Le classifieur LLM (`AnthropicClassifier`) est branché et testé (sortie
  structurée validée par schéma, repli en statut « incertain » — jamais une
  exception ni une supposition silencieuse — sur erreur API, timeout ou refus,
  §5.5.4). Modèle par défaut : Haiku 4.5 (`classification_model` dans les
  settings), à ajuster selon le taux de pertinence mesuré en cohorte pilote
  (§2.2). Sans `ANTHROPIC_API_KEY` configurée, le squelette reste sur le
  fallback par règles (`RuleBasedFallbackClassifier`) — pratique pour les
  tests et le développement local sans clé API.
- **`RuleBasedFallbackClassifier` est utilisable comme classification
  principale du MVP à coût zéro**, pas seulement comme filet de secours :
  aucune clé Anthropic n'est nécessaire pour faire tourner le pilote (à la
  qualité près d'un LLM sur les tournures ambiguës, cf. §5.5.4). Deux
  défauts corrigés pour le rendre fiable dans ce rôle :
  - `GlossaryService.match_expressions`/`match_entries` matchaient sur
    simple sous-chaîne : `"deal"` matchait à tort dans `"l'idéal"`, `"non"`
    dans `"sinon"` — courant en français avec des expressions courtes d'une
    syllabe. Corrigé par un match sur frontière de mot (regex lookaround).
  - Le score de pertinence comptait toute expression du glossaire matchée à
    poids égal, y compris les entrées `autre` (ex. `"gaou"` : moqueur, pas
    une intention d'achat — cf. commentaire dans `seed_glossary.py`) : une
    interpellation ou un signal négatif boostait le score au même titre
    qu'une vraie intention d'achat. Corrigé par une pondération par
    catégorie (`_POIDS_CATEGORIE_GLOSSAIRE` dans `classifier.py`) —
    `intention_achat` compte, `autre` non.
  Vérifié en tests et en live contre un Postgres réel avec le glossaire
  seedé (`ok deal, je prends la robe wax` → 0.75 ; `sois pas gaou,
  fais-moi un prix` → 0.0 ; `c'est l'ideal pour moi` → 0.0, aucun faux
  positif sur `deal`).
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
  branché de bout en bout (service + API), testé avec 13 tests dont un test
  d'intégration API complet (`tests/test_live_api.py`). `POST /reservations/{id}/expirer`
  reste disponible pour un déclenchement manuel/externe, mais l'expiration
  est désormais aussi automatique (voir `scheduler.py` ci-dessous).
- Catalogue produit minimal (`models/product.py`, `POST`/`GET /businesses/{id}/products`) :
  relie `Reservation.article_ref` (saisie libre pendant un live) à un prix
  réel via `Product.reference` — pas de clé étrangère directe, un article
  peut être commenté avant d'être catalogué. Si aucun `Product` ne
  correspond à l'activation d'une réservation, le montant reste à `0.0`
  (avec un log d'avertissement) plutôt que de bloquer le live en cours.
  Référence non réutilisable deux fois pour un même `Business` (contrainte
  unique `business_id` + `reference`, 409 sinon).
- Commission de 5% sur les ventes live confirmées via TikTok (§6) : calculée
  et enregistrée sur `Transaction.commission_montant` à la confirmation du
  paiement (`confirmer_paiement`), uniquement si le canal du live est
  `tiktok_own` — `None` (pas `0.0`) pour les autres rails/canaux, afin de
  distinguer « pas de commission applicable » de « commission nulle
  calculée ». Vérifié en tests et contre un Postgres réel (produit
  catalogué à 15 000 XOF → commission de 750 XOF à la confirmation).
- `ReportScheduler` regroupe les `Signal` au statut `nouveau` au-dessus du
  seuil `Business.seuil_pertinence`, sur une fenêtre glissante (fin du
  dernier rapport → maintenant, plutôt qu'un alignement calendaire par
  fuseau horaire — `Business.fuseau_horaire` n'est pas encore exploité ici).
  Aucun rapport vide n'est envoyé. `POST /reports/generer` reste disponible
  pour un déclenchement manuel/externe, mais la génération est désormais
  aussi automatique (voir `scheduler.py` ci-dessous).
- `src/trakist/scheduler.py` : ordonnanceur interne (APScheduler,
  `BackgroundScheduler`) démarré/arrêté avec le cycle de vie de l'app
  FastAPI (`lifespan` dans `api/main.py`). Deux jobs périodiques appellent
  directement les services existants avec leur propre session DB :
  génération des rapports dus (15 min par défaut) et expiration des
  réservations live dues (1 min par défaut, cohérent avec la fenêtre de
  paiement de 5 min — `DEFAULT_FENETRE_EXPIRATION`). Remplace le besoin d'un
  worker externe (cron, Celery beat...) pour un déploiement mono-instance ;
  configurable via `SCHEDULER_ENABLED` et les deux intervalles
  (`config.py`) — à désactiver si le service passe multi-instance sans
  ordonnanceur externe partagé, pour éviter un déclenchement en double.
- `GET /admin/dashboard` (§3.5) : taux de pertinence par couple (pays,
  secteur) — une « cohorte » pilote n'a pas d'entité dédiée dans le modèle,
  le secteur en fait office (§2.2) — avec seuil d'alerte à 70% (§2.2), et
  santé des connecteurs par pays/type/statut. Le suivi des coûts d'API par
  entrepreneur (§3.5) n'est pas couvert : aucune instrumentation de coût
  n'existe encore dans l'architecture.
- Onboarding entrepreneur (§3.1) complet côté API : `POST /businesses/{id}/offers`
  et `POST /businesses/{id}/channels` (404 si le `Business` n'existe pas).
  Un `Channel` créé via l'API est considéré `connecte` par défaut — la
  création représente l'étape « bot ajouté / compte lié » déjà effectuée par
  l'entrepreneur, pas un état intermédiaire à confirmer séparément.
- Moteur de veille (§3.2) branché de bout en bout : `POST /channels/{id}/messages`
  classifie un message contre chaque `Offer` du `Business` et crée le
  `Signal` correspondant (meilleure correspondance conservée) — vérifié en
  tests et contre un Postgres réel. C'est le point d'entrée qu'un
  consommateur de la file Redis (`queue.py`) appellera une fois de vrais
  connecteurs branchés (§5.2).
- Boucle de correction humaine (§3.3, §5.5.3) complète : `POST /webhooks/whatsapp/feedback`
  consomme la réponse OUI/NON d'un entrepreneur (format généré par
  `send_feedback_prompt`, ex. `"OUI (ref <signal_id>)"`) et met à jour le
  `Signal`. Comme pour le webhook de paiement, le format exact d'un webhook
  WhatsApp Business réel (Meta Cloud API) n'est pas modélisé — seul le texte
  du message, une fois extrait, est traité ici.
- Sécurité des webhooks entrants (`api/security.py`) : `POST /webhooks/payments/momo`
  et `POST /webhooks/whatsapp/feedback` exigent un header `X-Webhook-Secret`
  vérifié contre `WEBHOOK_SHARED_SECRET` (comparaison à temps constant).
  **Fail closed** : secret non configuré (défaut) → tous les appels
  rejetés (503), pas de webhook exploitable par defaut. Provisoire en
  attendant la vérification de signature réelle par fournisseur (HMAC
  MTN/Orange, vérification Meta Cloud API) une fois les identifiants par
  pays disponibles (§5.2) — sans ça, n'importe qui connaissant une
  référence de transaction pouvait jusqu'ici forger une confirmation de
  paiement ou usurper le feedback WhatsApp d'un entrepreneur. Le reste de
  l'API (`/businesses/*`, `/signals/*`, `/admin/*`...) n'a en revanche
  toujours aucune authentification — à traiter dans un chantier séparé,
  plus large (clé API par `Business` + protection des routes admin).
- Deux bugs trouvés en vérifiant le flux complet contre un Postgres réel
  (invisibles avec la seule suite pytest, qui tourne sur SQLite) :
  - Les `logger.info(...)` des stubs WhatsApp/paiement (§5.2) n'apparaissaient
    nulle part car aucun `logging.basicConfig` n'était appelé — le logger
    racine reste à `WARNING` par défaut. Corrigé dans `api/main.py`.
  - `ReportScheduler` et `LiveReconciliationService` comparaient/soustrayaient
    des `datetime` : Postgres renvoie des valeurs *aware* pour une colonne
    `DateTime(timezone=True)`, SQLite les renvoie toujours *naive* quel que
    soit le flag — ce qui masquait le bug en tests tout en le faisant planter
    (`TypeError: can't subtract offset-naive and offset-aware datetimes`) dès
    qu'un `Business` avait un rapport ou une réservation déjà en base. Corrigé
    via `trakist/timeutils.py` (`utcnow()` / `as_naive_utc()`), utilisé pour
    toute comparaison entre une valeur générée en Python et une valeur relue
    depuis la base.
