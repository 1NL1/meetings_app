# MeetWise

Application web de gestion de réunions : transcription audio, génération de comptes-rendus, RAG sur les documents.

## Prérequis

- **Docker** (v20+) — [installer Docker Desktop](https://docs.docker.com/get-docker/)
- **Docker Compose** — inclus dans Docker Desktop, ou `brew install docker-compose`
- **Une clé API Mistral** — obtenue sur [console.mistral.ai](https://console.mistral.ai)

Vérifier que tout est installé :
```bash
docker --version          # Docker version 29.x.x
docker-compose --version  # Docker Compose version 5.x.x
```

## Lancement pas à pas

### Étape 1 — Se placer dans le dossier du projet

```bash
cd meetwise
```

### Étape 2 — Configurer les variables d'environnement

Copier le template et remplir les valeurs :
```bash
cp .env.example .env
```

Ouvrir `.env` et remplir :
```env
MISTRAL_API_KEY=ta_clé_api_mistral_ici
JWT_SECRET=une_clé_secrète_générée    # générer avec : openssl rand -hex 32
```

Les autres valeurs peuvent rester par défaut.

### Étape 3 — Lancer les conteneurs

```bash
docker-compose up --build
```

Cette commande :
1. Construit l'image du **backend** (Python 3.12 + FastAPI)
2. Construit l'image du **frontend** (Node 20 + React, servi par nginx)
3. Démarre **PostgreSQL 16**
4. Démarre le backend sur le port **8000**
5. Démarre le frontend sur le port **3000**

Attendre que les 3 conteneurs soient lancés. Tu verras dans les logs :
```
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend-1  | ... ready ...
postgres-1  | ... database system is ready to accept connections
```

### Étape 4 — Appliquer les migrations de base de données

Dans un **second terminal** (le premier est occupé par docker-compose) :

```bash
cd meetwise
docker-compose exec backend alembic upgrade head
```

Cela crée les tables `users`, `meetings`, `templates` dans PostgreSQL.

### Étape 5 — Accéder à l'application

| Service | URL |
|---|---|
| Frontend (interface) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Documentation API (Swagger) | http://localhost:8000/docs |

1. Ouvrir http://localhost:3000
2. Créer un compte (email + mot de passe + nom)
3. Se connecter
4. Commencer à utiliser l'application

## Commandes utiles

```bash
# Lancer en arrière-plan (mode détaché)
docker-compose up --build -d

# Voir les logs
docker-compose logs -f

# Voir les logs d'un seul service
docker-compose logs -f backend

# Arrêter les conteneurs
docker-compose down

# Arrêter et supprimer les volumes (reset complet de la DB)
docker-compose down -v

# Créer une nouvelle migration après modification d'un modèle
docker-compose exec backend alembic revision --autogenerate -m "description du changement"

# Appliquer les migrations
docker-compose exec backend alembic upgrade head
```

## Structure des services

```
docker-compose.yml
├── postgres    (port 5432) — Base de données PostgreSQL 16
├── backend     (port 8000) — API FastAPI + uvicorn
└── frontend    (port 3000) — React + nginx (proxy /api → backend)
```
