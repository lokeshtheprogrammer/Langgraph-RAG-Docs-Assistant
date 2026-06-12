# PHASE_6_DEPLOYMENT.md — Phase 6: Deployment
## RAG-Based Technical Documentation Assistant

---

## 1. Phase Goal

*   **Business Goal**: Make the application package portable and deployable to production/staging servers with single-command build procedures.
*   **Technical Goal**: Create Dockerfile and docker-compose configurations, and define automated continuous integration workflows in GitHub Actions.
*   **Completion Criteria**: Executing `docker compose up` compiles the application container, seeds the vector database, starts the uvicorn REST server, and processes incoming query requests.

---

## 2. Scope

### Included
*   Dockerfile using secure, lightweight Python bases.
*   Docker Compose configuration mapping persistent volume stores for SQLite databases and ChromaDB files.
*   Continuous integration (CI) workflow inside GitHub Actions checking lints and running test suite.
*   Automated setup scripts (`scripts/setup_env.sh`, `scripts/reset_db.sh`).
*   Execution verification script testing endpoints.

### Excluded
*   Kubernetes charts (Helm).
*   Production SSL certificate provisioning.

---

## 3. Dependencies

*   Phases 1 to 5 completed successfully.
*   Local docker engine installed.

---

## 4. Deliverables

*   `Dockerfile`
*   `docker-compose.yml`
*   `.dockerignore`
*   `.github/workflows/ci.yml`
*   `scripts/setup_env.sh`
*   `scripts/reset_db.sh`
*   `scripts/run_smoke_tests.sh`

---

## 5. Sub-Phases

### Phase 6.1: Docker Containerization & Volume Scaffolding
*   **Goal**: Create production container images and setup compose volume configurations.
*   **Tasks**:
    1. Write `.dockerignore` file.
    2. Write `Dockerfile` using `python:3.11-slim` base. Ensure non-root execution profiles.
    3. Write `docker-compose.yml` mapping directories `./data` and `./chroma_db` to local directory locations.
*   **Files**:
    - `Dockerfile`
    - `docker-compose.yml`
    - `.dockerignore`
*   **Acceptance Criteria**: Running `docker compose build` completes without errors and compiles image layers.
*   **Verification**: Check image builds using standard docker console.

---

### Phase 6.2: CI Workflows & Operational Utilities
*   **Goal**: Create automated CI pipelines and write database reset/smoke test scripts.
*   **Tasks**:
    1. Write `.github/workflows/ci.yml` linting code (Ruff) and running the test suite on branch pushes.
    2. Write utility setup/reset scripts in `scripts/` folder.
    3. Write automated query execution tests verifying API outputs.
*   **Files**:
    - `.github/workflows/ci.yml`
    - `scripts/setup_env.sh`
    - `scripts/reset_db.sh`
    - `scripts/run_smoke_tests.sh`
*   **Acceptance Criteria**: GitHub Actions pipeline passes on push tasks. Shell scripts initialize environments and start container tests.
*   **Verification**: Run setup/reset scripts locally and check data structures.

---

## 6. AI Build Prompt (`AI_BUILD_PROMPT.md`)

```markdown
# AI Build Prompt: Phase 6 (Deployment)

## Goal
Establish containerization and automated verification workflows.

## Files to Create/Modify
- **Dockerfile**: Use `python:3.11-slim`. Set workspace directory `/app`. Copy configurations, install requirements, expose port 8000, and define non-root user setups.
- **docker-compose.yml**: Configure app service mapping exposed port `8000:8000`. Define persistent volume mappings for SQLite registries `./data` and ChromaDB files `./chroma_db`. Add environment config bindings.
- **.dockerignore**: Exclude `.git`, `__pycache__`, `.venv`, `chroma_db/`, `data/*.db`, and test cache files.
- **.github/workflows/ci.yml**: GitHub Actions flow:
  - Setup python runtime environment (3.11).
  - Install dependencies.
  - Run Ruff checks.
  - Run Pytest test suites.
- **scripts/setup_env.sh**: Installs virtual environments and dependencies.
- **scripts/reset_db.sh**: Cleans local ChromaDB and SQLite databases.
- **scripts/run_smoke_tests.sh**: Submits curl calls to local running API and asserts response states.

## Constraints
- Containers must run using non-privileged users to respect basic container security best practices.
- Ensure volume mounts retain permissions, allowing databases writes.
```

---

## 7. Verification Package

### Manual Verification
1. Build and start containers:
   ```bash
   docker compose up --build -d
   ```
2. Seed database inside container:
   ```bash
   docker compose exec app python ingestion/ingest_corpus.py
   ```
3. Run operational smoke tests check:
   ```bash
   bash scripts/run_smoke_tests.sh
   ```

### Expected Results
*   Container initializes and stays active.
*   Ingestion script seeds vector databases inside container.
*   Smoke tests script validates API connectivity.

### Failure Conditions
*   Containers exit with database permission denied failures.
*   Volume bounds erase index details on restarts.

---

## 8. Review Gates

- [ ] Docker builds run successfully.
- [ ] Containers run as non-root users.
- [ ] Data volumes persist correctly on restarts.
- [ ] CI workflow executes Ruff and Pytest pipelines cleanly.
- [ ] Smoke tests check query outputs.
