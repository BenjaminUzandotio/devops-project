# User API DevOps Project

Python/FastAPI CRUD service with PostgreSQL storage, automated tests, CI, containerization, Kubernetes manifests, and IaC (Vagrant + Ansible). Includes health and metrics endpoints plus Docker/K8s/Vagrant workflows.

## Features and Work Done
- FastAPI CRUD on `/users` with SQLAlchemy models and pydantic schemas; uniqueness guard on email.
- Health endpoint `/health` hitting the database, metrics `/metrics` (cpu/memory) and request timing middleware (bonus monitoring).
- Tests: unit/API on in-memory SQLite, integration test against real Postgres via `TEST_DATABASE_URL`.
- CI (GitHub Actions) with flake8, tests, and multi-arch Docker build/push.
- Dockerfile (non-root), `.dockerignore`, docker-compose for app + Postgres.
- Kubernetes manifests for app + Postgres with persistent volume claim.
- Vagrant + Ansible provisioning to install Docker and run the stack from the synced folder; health check verification.

## Screenshots
- CI green: `screenshots/ci_success.png`
- Swagger UI: `screenshots/app_swagger.png`
- K8s pods running: `screenshots/k8s_pods_running.png`

## Run Locally (without containers)
```bash
cd userapi
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/userdb"  # please adjust as needed
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
curl http://localhost:8000/health
```

## Docker
```bash
cd userapi
docker build -t benjo55/userapi:latest .
docker run -p 8000:8000 -e DATABASE_URL="postgresql+psycopg://user:password@host.docker.internal:5432/userdb" benjo55/userapi:latest
```

### Docker Compose (app + Postgres)
```bash
cd userapi
docker compose up -d
curl http://localhost:8000/health
```

## Tests
Note: For integration tests, ensure a Postgres database is running (e.g., via Docker Compose).
```bash
cd userapi
# 1. Start DB for integration tests
docker compose up -d db

# 2. Run tests
pytest -v -m "not integration"
TEST_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/test_db" pytest -v -m "integration"
```

## CI/CD
- GitHub Actions workflow: `.github/workflows/ci.yaml`
- Steps: checkout, Python 3.11, cache deps, flake8, unit/API tests (SQLite), integration tests (Postgres service), then buildx multi-arch and push.
- Secrets needed: `DOCKER_USERNAME`, `DOCKER_PASSWORD`.

## Docker Hub
- Image: `benjo55/userapi:latest`
- Link: https://hub.docker.com/r/benjo55/userapi

## Kubernetes
```bash
kubectl apply -f k8s/db.yaml
kubectl apply -f k8s/app.yaml
kubectl get pods
```
Environment passed via `DB_HOST/DB_USER/DB_PASS/DB_NAME/DB_PORT` in `k8s/app.yaml`.

## Access the API
- Docker Desktop (Mac/Windows): The service is exposed on `http://localhost` (Port 80).
- Minikube: Run `minikube service userapi-service` --url to get the IP.

Environment passed via `DB_HOST/DB_USER/DB_PASS/DB_NAME/DB_PORT` in `k8s/app.yaml`.

## IaC: Vagrant + Ansible
```bash
cd iac
vagrant up          # provisions Ubuntu VM, installs Docker, starts the stack via docker compose
vagrant ssh
curl http://localhost:8000/health
```
Sync folder `/vagrant/userapi` is used to run the compose stack (API + Postgres) and Ansible waits for the health endpoint.

## API Quick Reference
- `GET /health` – DB-backed health check
- `GET /metrics` – process metrics
- `POST /users` – create user
- `GET /users` – list users (skip/limit)
- `GET /users/{id}` – read one
- `PUT /users/{id}` – update
- `DELETE /users/{id}` – delete

## Author
- Benjamin Uzan

## AI Usage
Project assisted by Gemini and Github Copilot in VsCode.


