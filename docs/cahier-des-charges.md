# Cahier des charges & architecture technique — v2
## Plateforme de veille commerciale et de réconciliation des ventes live — Bénin, Côte d'Ivoire, Sénégal

*Document de travail destiné à être utilisé comme brief de conception avec Claude Code. Nom de produit : **Trakist** — de l'anglais *track* et du suffixe français *-iste* (« spécialiste de track »). Remplace la v1 mono-pays / mono-verticale et le nom provisoire MarketRadar.*

---

## 1. Vision et problème résolu

Les entrepreneurs ouest-africains (e-commerçants, vendeurs en live sur TikTok/Facebook, artisans, commerçants tous secteurs confondus) font face à deux douleurs concrètes :

1. **Accès au marché** : ils n'ont ni le temps ni les outils pour repérer, parmi les publications, commentaires et recherches quotidiennes, les personnes qui expriment un besoin correspondant à leur offre — quelle que soit cette offre (mode, agroalimentaire, cosmétique, services, artisanat, etc.).
2. **Chaos opérationnel du live selling** : pendant une vente en direct, les commentaires d'achat arrivent plus vite que le vendeur ne peut les traiter, et l'attribution des articles se fait au jugé plutôt que sur preuve de paiement, générant litiges et ventes perdues.

**Trakist** répond aux deux à la fois : un moteur de détection d'intention d'achat sur les canaux pertinents, livré sous forme de rapport actionnable, et un module de réconciliation automatique commentaire → paiement → attribution pour les ventes en direct.

**Ce qui change dans cette v2 par rapport à la v1 :**
- Lancement simultané sur **3 pays** (Bénin, Côte d'Ivoire, Sénégal) au lieu d'un seul, en misant sur leur proximité linguistique et culturelle (argot commercial de rue partagé en partie, notamment via la diffusion du Nouchi ivoirien dans l'espace urbain ouest-africain).
- Le produit **n'est plus limité à l'agroalimentaire** : le moteur est générique dès le départ et s'adapte à l'offre déclarée par chaque entrepreneur, tous secteurs confondus.
- Le moteur de classification doit gérer le **code-switching français/anglais** (expressions anglaises mêlées au français dans le langage courant/de rue), sans pour autant que l'interface et les rapports soient traduits en anglais au lancement — l'anglais complet de l'interface est repoussé en V2, en préparation d'une expansion vers des marchés anglophones (Ghana, Nigeria).

---

## 2. Périmètre du lancement

### 2.1 Ce qui est construit dès le MVP (socle large, ouverture progressive)
- **3 pays dès la conception de l'architecture** : chaque pays est un "profil marché" configurable (langue dominante, argots locaux, canaux disponibles, rail de paiement mobile money), pas un fork séparé du produit.
- **Multi-vertical dès le départ** : l'entrepreneur déclare librement son offre (mots-clés, secteur, zone) ; aucune logique métier codée en dur par verticale.
- **Moteur de classification bilingue FR/EN** capable de repérer une intention d'achat même quand le message mélange les deux langues, avec prise en compte des argots locaux par pays (voir §5.5).

### 2.2 Comment on ouvre réellement l'accès (séquencement)
Pour éviter de tester quatre inconnues à la fois (3 pays × multi-vertical × bilingue × argot) sans pouvoir isoler ce qui marche ou pas, l'ouverture se fait par **cohortes pilotes restreintes** :
- Phase pilote : une dizaine d'entrepreneurs par pays, recrutés à la main, sur 2-3 secteurs volontairement choisis pour leur diversité (ex. mode, agroalimentaire, cosmétique) afin de stress-tester le moteur de classification sur des types de signaux différents.
- Chaque pilote alimente une boucle de correction humaine ("ce prospect n'était pas pertinent" / "tu as raté celui-là") qui vient enrichir le glossaire d'argot local et les prompts de classification.
- Ouverture large par pays uniquement une fois le taux de pertinence des rapports validé sur la cohorte pilote (seuil à définir, ex. >70% de signaux jugés pertinents par les pilotes).

### 2.3 Canaux couverts au lancement
- Groupes Facebook et WhatsApp **dont l'entrepreneur est déjà membre** (bot ajouté avec son autorisation — pas de scraping externe).
- TikTok : commentaires et lives du **compte propre** de l'entrepreneur (accès légitime via les outils créateur).
- Recherche Google (API de recherche) pour les mentions publiques (forums, annonces, blogs).
- Canal de livraison des rapports : WhatsApp exclusivement au lancement.
- Paiement : MTN MoMo et/ou Orange Money selon disponibilité par pays (Orange Money est présent en Côte d'Ivoire et Sénégal ; à vérifier pays par pays pour MTN MoMo au Bénin).

Hors périmètre au lancement (repoussé en V1/V2) : Twitter/X, hashtags TikTok tiers via fournisseur de données, dashboard web, interface anglaise complète, expansion anglophone.

---

## 3. Fonctionnalités du produit

### 3.1 Onboarding entrepreneur
- Inscription via WhatsApp ou formulaire léger : nom, secteur (libre, non limité à une liste fermée), ville, pays, offres/produits, mots-clés associés, numéro mobile money.
- Sélection de la langue de communication de l'entrepreneur (français par défaut sur les 3 pays de lancement).
- Connexion des canaux : ajout du bot aux groupes Facebook/WhatsApp, lien du compte TikTok créateur.
- Configuration du rythme de rapport (quotidien / hebdomadaire) et du fuseau horaire d'envoi.

### 3.2 Moteur de veille et détection d'intention
- Ingestion continue des canaux configurés.
- Classification par LLM de chaque message/commentaire/résultat de recherche selon :
  - correspondance avec l'offre déclarée (produit/service, secteur, zone géographique) — logique identique quel que soit le secteur,
  - présence d'un signal d'intention d'achat, y compris en cas de mélange français/anglais ou d'expressions d'argot local,
  - score de pertinence et score de confiance linguistique (le système doit pouvoir signaler "je ne suis pas sûr de comprendre cette expression" plutôt que de deviner en silence).
- Seuil de pertinence configurable pour éviter la fatigue du rapport.

### 3.3 Rapport de prospection
- Envoi WhatsApp automatique (quotidien/hebdo) : source, extrait du message, lien si disponible, score de pertinence, action suggérée.
- Bouton de retour rapide ("pertinent" / "pas pertinent") directement dans le message WhatsApp pour alimenter la boucle d'amélioration du moteur.
- Historique consultable à la demande.

### 3.4 Module de réconciliation des ventes live
(Identique dans son principe à la v1, généralisé à tous les secteurs, pas seulement l'agroalimentaire)
- Détection en temps réel des commentaires d'intention d'achat sur les lives/vidéos du compte de l'entrepreneur.
- File d'attente ordonnée par ordre d'arrivée du commentaire.
- Déclenchement automatique d'une demande de paiement (Request-to-Pay MTN MoMo / Orange Money) vers le premier de la file.
- Verrouillage temporaire de l'article, fenêtre configurable.
- Paiement confirmé (webhook) → attribution actée, notifications ; délai dépassé → libération automatique au suivant.
- Journal de transaction traçable en cas de litige.

### 3.5 Administration interne
- Suivi de l'usage, santé des connecteurs, coûts d'API par entrepreneur et par pays.
- Tableau de bord pilote : suivi du taux de pertinence par cohorte/pays, pour décider du passage à l'ouverture large.

---

## 4. Modèle de données (entités principales, mises à jour)

```
Country (profil marché)
 ├── code (BJ | CI | SN)
 ├── langue_dominante (fr)
 ├── rails_paiement_disponibles[] (momo, orange_money)
 └── glossaire_argot_ref → GlossaryEntry[]

GlossaryEntry (argot / expressions locales)
 ├── country_code
 ├── expression, signification, exemple_usage
 ├── categorie (intention_achat | question | négociation | autre)
 └── source (curation manuelle | remontée pilote)

Business (entrepreneur)
 ├── id, nom, secteur (libre), ville, country_code
 ├── numero_paiement_momo
 ├── frequence_rapport (daily/weekly)
 └── canaux_connectes[] → Channel

Offer (offre déclarée — inchangé, générique par nature)
 ├── business_id
 ├── libellé produit/service, mots-clés associés, zone_geo_cible

Channel
 ├── type (facebook_group | whatsapp_group | tiktok_own | google_search)
 ├── business_id, identifiant externe, statut_connexion

Signal (prospect détecté)
 ├── channel_id, business_id, offer_id
 ├── texte_source, url_source, auteur
 ├── langue_detectee (fr | en | mixte), expressions_argot_matchées[]
 ├── score_pertinence, score_confiance_linguistique
 ├── statut (nouveau | envoyé_au_rapport | jugé_pertinent | jugé_non_pertinent)
 └── date_detection

Report / LiveSession / LiveComment / Reservation / Transaction
 (inchangés dans leur structure par rapport à la v1)
```

Le changement structurel majeur par rapport à la v1 : l'ajout de **Country** et **GlossaryEntry** comme entités de premier plan, qui alimentent dynamiquement le prompt de classification — c'est ce qui permet de partager un seul moteur entre les 3 pays sans dupliquer le code.

---

## 5. Architecture technique

### 5.1 Vue d'ensemble

```mermaid
flowchart TB
    subgraph Sources["Sources externes (par pays)"]
        FB[Groupes Facebook/WhatsApp\nautorisés]
        TT[Compte TikTok propre]
        GG[Recherche Google]
        MOMO[MTN MoMo / Orange Money]
    end

    subgraph Ingestion["Couche d'ingestion"]
        C1[Connecteur Facebook/WhatsApp]
        C2[Connecteur TikTok]
        C3[Connecteur Recherche Web]
        C4[Connecteur Paiement]
    end

    subgraph MarketCtx["Service de contexte marché"]
        GLOSS[Glossaires d'argot\npar pays: BJ / CI / SN]
        LANGDET[Détecteur de langue\n+ code-switching FR/EN]
    end

    subgraph Core["Coeur applicatif"]
        Q[File de messages\n(Redis/SQS)]
        NLP[Service de classification IA\n(LLM + contexte marché injecté)]
        VE[Moteur de veille → Signal]
        LR[Moteur de réconciliation live]
        SCHED[Ordonnanceur de rapports]
        FEEDBACK[Boucle de correction humaine\n(pertinent / pas pertinent)]
    end

    subgraph Data["Stockage"]
        DB[(PostgreSQL)]
        CACHE[(Redis)]
    end

    subgraph Delivery["Livraison"]
        WA[API WhatsApp Business]
    end

    FB --> C1 --> Q
    TT --> C2 --> Q
    GG --> C3 --> Q
    Q --> LANGDET --> NLP
    GLOSS --> NLP
    NLP --> VE --> DB
    VE --> SCHED --> WA
    WA --> FEEDBACK --> GLOSS

    C2 --> LR
    MOMO --> C4 --> LR
    LR --> DB
    LR --> WA

    DB <--> CACHE
```

### 5.2 Détail des connecteurs

| Connecteur | Mode d'accès | Contrainte principale |
|---|---|---|
| Facebook/WhatsApp groupes | Bot ajouté par l'entrepreneur | API Graph limitée pour la recherche libre |
| TikTok (compte propre) | Outils créateur / API officielle | Pas d'accès aux lives d'autres comptes sans fournisseur tiers (hors périmètre) |
| Recherche Google | API de recherche | Coût par requête à surveiller à l'échelle 3 pays |
| MTN MoMo / Orange Money | API officielle Request-to-Pay + webhook | Disponibilité du rail à vérifier pays par pays (Orange Money confirmé CI/SN, à valider pour le Bénin) |

### 5.3 Stack technique suggérée

- **Backend** : services séparés (ingestion, contexte marché, classification, réconciliation, notification), Python/FastAPI.
- **File de messages** : Redis Streams ou SQS.
- **Classification IA** : appel LLM avec prompt structuré, **enrichi dynamiquement** par le glossaire du pays concerné et l'historique de corrections de la cohorte pilote — pas un prompt statique unique pour les 3 pays.
- **Base de données** : PostgreSQL.
- **Notifications** : API WhatsApp Business officielle.
- **Hébergement** : cloud avec latence raisonnable vers l'Afrique de l'Ouest.
- **Observabilité** : suivi par pays du taux de pertinence des signaux, distinct par cohorte pilote, pour piloter la décision d'ouverture large.

### 5.4 Flux critique : réconciliation d'une vente live
(Inchangé par rapport à la v1 — voir schéma détaillé du flux commentaire → réservation → Request-to-Pay → confirmation/expiration dans les échanges précédents. Ce module est agnostique du pays et du secteur, seule la devise/le rail de paiement varie.)

### 5.5 Traitement linguistique — le cœur de la difficulté de cette v2

C'est le point technique le plus sensible du projet, à traiter avec le plus de rigueur :

1. **Détection de langue et de code-switching** : chaque message entrant passe par une étape de détection (français pur / anglais pur / mélange) avant classification — un message peut être majoritairement français avec des emprunts anglais ("j'suis chaud pour ça", "let's go pour la commande").
2. **Glossaire d'argot par pays, pas un glossaire unique** : même si les 3 pays partagent une base commune, chaque pays a ses expressions propres. Le glossaire doit être structuré par `country_code`, avec un socle partagé (expressions communes à l'espace ouest-africain francophone) et une couche spécifique par pays.
3. **Le glossaire n'est pas figé au lancement** : il démarre avec une curation manuelle minimale (locuteurs natifs par pays, quelques dizaines d'expressions clés liées à l'achat/la négociation) et s'enrichit via la boucle de correction humaine issue des pilotes (§2.2 et §4).
4. **Score de confiance obligatoire** : si le moteur n'est pas sûr d'avoir compris une expression, le signal doit être marqué comme incertain plutôt que classé silencieusement comme non pertinent (risque de rater un vrai prospect) ou pertinent (risque de bruit). Cette incertitude peut remonter dans un canal de vérification humaine pendant la phase pilote.

---

## 6. Modèle de monétisation
- **Veille commerciale (market tracking)** : abonnement mensuel à partir de 4 900 FCFA par canal connecté (Facebook, WhatsApp, TikTok, recherche Google — §5.2), en monnaie locale via mobile money. Au-delà d'un usage standard (volume de canaux/messages élevé), tarification sur devis.
- **Réconciliation de ventes live** : commission de 5% sur les transactions confirmées via le module de réconciliation live TikTok (§3.4, §5.4) — prélevée uniquement sur un paiement effectivement confirmé, jamais sur une réservation expirée ou non payée.
- Tarification à affiner avec les cohortes pilotes de chaque pays — le pouvoir d'achat et les habitudes de paiement diffèrent légèrement entre Bénin, Côte d'Ivoire et Sénégal, à ne pas supposer identiques.

---

## 7. Risques et points d'attention (mis à jour)

- **Cumul des inconnues** : 3 pays + multi-vertical + bilingue + argot en simultané. Mitigé par le séquencement en cohortes pilotes restreintes (§2.2) — ne pas ouvrir large tant que le taux de pertinence n'est pas validé pays par pays.
- **Qualité du glossaire au lancement** : un glossaire trop pauvre au démarrage produit des rapports peu pertinents. Prévoir un travail de curation initiale avec des locuteurs natifs de chaque pays avant même le premier pilote, pas seulement une amélioration a posteriori.
- **Disparité des rails de paiement** : ne pas supposer que MTN MoMo et Orange Money sont disponibles et équivalents dans les 3 pays — à vérifier précisément avant de coder l'intégration.
- **Accès TikTok tiers** : inchangé par rapport à la v1, toujours hors périmètre au lancement.
- **Conformité données personnelles** : les régimes de protection des données diffèrent entre Bénin, Côte d'Ivoire et Sénégal (autorités et textes distincts) — à vérifier pays par pays, pas de présomption d'un régime unique ouest-africain.

---

## 8. Roadmap suggérée

| Phase | Contenu |
|---|---|
| **MVP** | Architecture 3 pays + multi-vertical dès la conception ; cohortes pilotes restreintes par pays (Bénin, Côte d'Ivoire, Sénégal) ; moteur bilingue FR/EN avec détection de code-switching ; interface et rapports en français uniquement |
| **V1** | Ouverture large par pays une fois le seuil de pertinence validé par pilote ; enrichissement continu des glossaires ; tableau de bord web léger optionnel |
| **V2** | Interface et rapports disponibles en anglais complet ; expansion vers des marchés anglophones (Ghana, Nigeria) ; élargissement de la veille (Twitter/X, hashtags TikTok tiers) ; deuxième rail de paiement par pays si pertinent |

---

## 9. Comment utiliser ce document avec Claude Code

Suggestions de premiers prompts :

1. *"Initialise un squelette de projet backend correspondant à l'architecture en §5, avec les entités du modèle de données en §4, en modélisant `Country` et `GlossaryEntry` comme configuration de premier plan."*
2. *"Implémente le service de contexte marché (§5.5) : détection de langue/code-switching + injection dynamique du glossaire par pays dans le prompt de classification."*
3. *"Construis le moteur de réconciliation live (§5.4) comme une machine à états, avec tests couvrant paiement confirmé, expiration, et gestion multi-devise (XOF pour les 3 pays, mais rails différents)."*
4. *"Propose un schéma PostgreSQL complet à partir du modèle de données en §4, avec les contraintes de `Country` en clé étrangère sur `Business` et `GlossaryEntry`."*
5. *"Construis le tableau de bord pilote interne (§3.5) pour suivre le taux de pertinence des signaux par pays et par cohorte."*

Décisions encore ouvertes à trancher avant mise en œuvre : verticales exactes à inclure dans les cohortes pilotes de chaque pays, disponibilité confirmée de MTN MoMo au Bénin, seuil précis de taux de pertinence déclenchant l'ouverture large par pays.
