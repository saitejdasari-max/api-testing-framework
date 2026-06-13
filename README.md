# 🚀 Enterprise API Testing Framework

A **production-grade API test automation framework** built with Python, pytest, and Allure — designed for scale, maintainability, and CI/CD integration.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Tech Stack](#tech-stack)
4. [Setup & Installation](#setup--installation)
5. [Configuration](#configuration)
6. [Running Tests](#running-tests)
7. [Writing Tests](#writing-tests)
8. [Reporting](#reporting)
9. [CI/CD Integration](#cicd-integration)
10. [Best Practices](#best-practices)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Test Layer                         │
│  tests/smoke/   tests/regression/   tests/integration/  │
└───────────────────────┬─────────────────────────────────┘
                        │ uses
┌───────────────────────▼─────────────────────────────────┐
│                   API Clients                           │
│       UsersClient    PostsClient    (+ your clients)    │
└───────────────────────┬─────────────────────────────────┘
                        │ inherits
┌───────────────────────▼─────────────────────────────────┐
│                   BaseClient                            │
│  _get / _post / _put / _patch / _delete                 │
└───────────────────────┬─────────────────────────────────┘
                        │ uses
┌───────────────────────▼─────────────────────────────────┐
│                 RequestWrapper                          │
│  Session  │  Retry (tenacity)  │  Logging  │  Allure    │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
  TokenManager   ConfigManager    DataManager
  (auth cache)   (env config)   (fixtures + Faker)
```

### Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Single Responsibility** | Each client manages one resource; each utility does one thing |
| **Config-Driven** | All environment settings in `.env` / YAML; zero hardcoding |
| **Fluent Assertions** | Chainable `ResponseValidator` for readable test expectations |
| **Fail-Fast + Retry** | `tenacity` retries on transient errors; tests fail clearly otherwise |
| **Schema-First** | Pydantic v2 models define the contract; validation is automatic |
| **Parallel-Ready** | Stateless clients + pytest-xdist for N-worker parallel runs |

---

## Project Structure

```
api_testing_framework/
│
├── api_clients/                  # Resource-specific API clients
│   ├── base_client.py            # Abstract base — CRUD passthrough + auth
│   ├── users_client.py           # /users resource
│   └── posts_client.py           # /posts resource
│
├── configs/                      # Environment configuration
│   ├── config_manager.py         # Pydantic config loader (singleton)
│   ├── dev.yaml                  # Optional dev-env YAML overrides
│   ├── staging.yaml              # Staging overrides
│   └── production.yaml           # Prod overrides
│
├── data/
│   ├── schemas/
│   │   └── models.py             # Pydantic v2 response schemas
│   └── test_data/
│       └── users.json            # Static fixture data
│
├── utils/
│   ├── logger.py                 # Coloured + file logger
│   ├── token_manager.py          # Thread-safe token cache
│   ├── request_wrapper.py        # Session + retry + Allure attach
│   ├── response_validator.py     # Fluent chainable validator
│   ├── assertions.py             # Domain-level custom assertions
│   └── data_manager.py           # JSON/YAML loaders + Faker factories
│
├── tests/
│   ├── smoke/
│   │   └── test_users_smoke.py
│   ├── regression/
│   │   ├── test_users_crud.py
│   │   └── test_posts_crud.py
│   └── integration/
│       └── test_cross_resource.py
│
├── logs/                         # Auto-generated log files
├── reports/
│   ├── html/                     # pytest-html reports
│   └── allure-results/           # Raw Allure JSON
│
├── .github/
│   └── workflows/
│       └── api_tests.yml         # GitHub Actions pipeline
│
├── conftest.py                   # Global fixtures + pytest hooks
├── pytest.ini                    # pytest configuration
├── requirements.txt
├── .env.example                  # Environment variable template
└── .gitignore
```

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.11+ | Core language |
| **pytest** | ≥7.4 | Test runner |
| **requests** | ≥2.31 | HTTP client |
| **pydantic v2** | ≥2.0 | Schema validation + config models |
| **allure-pytest** | ≥2.13 | Rich HTML/interactive reports |
| **pytest-html** | ≥4.0 | Lightweight standalone HTML reports |
| **pytest-xdist** | ≥3.3 | Parallel test execution |
| **pytest-rerunfailures** | ≥12 | Automatic test retry |
| **tenacity** | ≥8.2 | Retry logic for HTTP requests |
| **faker** | ≥19 | Dynamic test data generation |
| **colorlog** | ≥6.7 | Coloured console logging |
| **python-dotenv** | ≥1.0 | `.env` file loading |
| **PyYAML** | ≥6.0 | YAML config overrides |

---

## Setup & Installation

### Prerequisites

- Python 3.11 or higher
- pip
- (Optional) Allure CLI for interactive reports — [install guide](https://allurereport.org/docs/install/)

### 1. Clone & enter the repo

```bash
git clone https://github.com/your-org/api-testing-framework.git
cd api-testing-framework
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your environment

```bash
cp .env.example .env
# Edit .env with your target API credentials
```

---

## Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `dev` | Active environment: `dev`, `staging`, `production` |
| `DEV_BASE_URL` | `https://jsonplaceholder.typicode.com` | Dev API base URL |
| `STAGING_BASE_URL` | _(empty)_ | Staging API base URL |
| `PROD_BASE_URL` | _(empty)_ | Production API base URL |
| `AUTH_USERNAME` | _(empty)_ | Auth username |
| `AUTH_PASSWORD` | _(empty)_ | Auth password |
| `API_KEY` | _(empty)_ | API key for key-based auth |
| `MAX_RETRIES` | `3` | HTTP request retry count |
| `RETRY_DELAY` | `2` | Seconds between retries |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |
| `LOG_TO_FILE` | `true` | Write logs to `logs/test_run.log` |

### Switching Environments

```bash
# Run against staging
ENV=staging pytest tests/smoke

# Run against production (smoke only — be careful!)
ENV=production pytest tests/smoke -m smoke
```

### YAML Overrides

Per-environment YAML files in `configs/` let you override any config key without touching `.env`. This is useful for CI matrix jobs:

```yaml
# configs/staging.yaml
environment:
  timeout: 60
retry:
  max_retries: 5
  retry_delay: 3
```

---

## Running Tests

### Basic run (all tests)

```bash
pytest
```

### By marker

```bash
pytest -m smoke                   # Smoke tests only
pytest -m regression              # Regression suite
pytest -m integration             # Integration tests
pytest -m "smoke or regression"   # Multiple markers
pytest -m "not slow"              # Exclude slow tests
```

### By directory

```bash
pytest tests/smoke/
pytest tests/regression/test_users_crud.py
pytest tests/regression/test_users_crud.py::TestUsersCRUD::test_create_user
```

### Parallel execution

```bash
pytest -n auto                    # Use all available CPU cores
pytest -n 4                       # Use exactly 4 workers
pytest -m regression -n auto      # Parallel regression run
```

### With HTML report

```bash
pytest --html=reports/html/report.html --self-contained-html
```

### With Allure report

```bash
pytest --alluredir=reports/allure-results
allure serve reports/allure-results   # Open interactive report in browser
```

### Retry on failure

```bash
pytest --reruns=3 --reruns-delay=2   # Retry each failing test up to 3 times
```

### Verbose with live log

```bash
pytest -v --log-cli-level=DEBUG
```

---

## Writing Tests

### 1. Create an API client

```python
# api_clients/orders_client.py
from api_clients.base_client import BaseClient
from requests import Response

class OrdersClient(BaseClient):
    RESOURCE = "orders"

    def get_order(self, order_id: int) -> Response:
        return self._get(order_id)

    def create_order(self, payload: dict) -> Response:
        return self._post(json=payload)
```

### 2. Add fixtures to `conftest.py`

```python
@pytest.fixture(scope="session")
def orders_client() -> OrdersClient:
    return OrdersClient()
```

### 3. Write the test

```python
import allure
import pytest
from utils.response_validator import validate
from utils.assertions import assert_created

@allure.epic("Order Management")
@allure.feature("CRUD")
@pytest.mark.regression
class TestOrdersCRUD:

    @allure.title("POST /orders — creates order and returns id")
    def test_create_order(self, orders_client, order_payload):
        response = orders_client.create_order(order_payload)

        validate(response) \
            .status(201) \
            .has_key("id") \
            .has_key("status") \
            .key_equals("status", "pending") \
            .matches_schema(OrderSchema) \
            .response_time_under(2000) \
            .assert_all()
```

### 4. Add a Pydantic schema

```python
# data/schemas/models.py
class OrderSchema(BaseModel):
    id: int = Field(gt=0)
    userId: int
    status: str
    items: list[OrderItemSchema]
    total: float = Field(gt=0)
```

### ResponseValidator API

```python
validate(response)
    .status(200)                          # Exact status code
    .status_in(200, 201)                  # One of several codes
    .success()                            # 200/201/202/204
    .has_key("id")                        # Key present in body
    .key_equals("status", "active")       # Key value match
    .key_type("id", int)                  # Key type check
    .body_is_list()                       # Body is JSON array
    .list_not_empty()                     # Array has ≥1 item
    .matches_schema(MyPydanticModel)      # Pydantic validation
    .content_type("application/json")     # Content-Type header
    .header_present("X-Request-Id")       # Any header present
    .response_time_under(1500)            # Elapsed ms < threshold
    .satisfies(lambda b: b["age"] > 18)  # Custom predicate
    .assert_all()                         # Raise if any failed
```

---

## Reporting

### pytest-HTML (lightweight)

Generated automatically at `reports/html/report.html` after every run.  
Open in any browser — fully self-contained single file.

### Allure (interactive)

```bash
# Generate results during test run
pytest --alluredir=reports/allure-results

# Serve interactive report locally
allure serve reports/allure-results

# Or generate static HTML
allure generate reports/allure-results -o reports/allure-html --clean
```

Allure reports include:
- Test status breakdown with timeline
- Per-test request/response JSON attachments
- Retry history
- Environment properties
- Behaviour tree (epic → feature → story → test)

### Logs

- **Console**: coloured output via `colorlog`
- **File**: `logs/test_run.log` (full DEBUG-level)
- **pytest log**: `logs/pytest.log`

---

## CI/CD Integration

### GitHub Actions

The workflow at `.github/workflows/api_tests.yml` provides:

| Job | Trigger | What it does |
|-----|---------|-------------|
| **smoke** | Every push / PR | Fast sanity check, blocks merge if failing |
| **regression** | Schedule + manual | Full suite on Python 3.11 and 3.12 matrix |
| **integration** | Schedule + manual | Cross-resource integrity tests |
| **publish-allure** | `main` branch | Deploys Allure report to GitHub Pages |

### Required GitHub Secrets

```
DEV_BASE_URL         https://your-dev-api.com
STAGING_BASE_URL     https://your-staging-api.com
PROD_BASE_URL        https://your-api.com
AUTH_USERNAME        ci_test_user
AUTH_PASSWORD        <secret>
API_KEY              <secret>
```

### Manual trigger

```
GitHub → Actions → API Test Suite → Run workflow
→ Choose environment (dev/staging/production)
→ Choose suite (smoke/regression/integration/all)
```

### Add to any CI system

```yaml
# Generic CI snippet
- name: Run API smoke tests
  env:
    ENV: staging
    STAGING_BASE_URL: ${{ env.API_URL }}
  run: |
    pip install -r requirements.txt
    pytest -m smoke -n auto --html=report.html
```

---

## Best Practices

### Test Design

- **One assertion per logical concern** — use `validate().assert_all()` to batch related checks, keep unrelated checks in separate test methods.
- **Parametrize boundary values** — use `@pytest.mark.parametrize` for IDs, pagination pages, and edge-case inputs.
- **Fixtures for state, not logic** — fixtures set up and tear down data; test methods contain the actual assertion logic.
- **Never hardcode URLs** — all base URLs come from `ConfigManager`.

### Data Management

- **Use factories for dynamic data** — `UserDataFactory.create_user()` generates unique payloads; never reuse the same static payload across tests.
- **Static fixtures for contract tests** — keep `data/test_data/*.json` for known reference values (e.g. "user with id=1 must have username=Bret").
- **Isolate test state** — each test should create its own data and not depend on data left by another test.

### Authentication

- **TokenManager is a singleton** — it caches tokens and refreshes them automatically. Never instantiate it directly in tests; let `BaseClient` handle it.
- **Override `_fetch_bearer_token`** — subclass `TokenManager` or monkey-patch it in `conftest.py` to connect your real auth endpoint.

### Performance

- **Run smoke in < 60 seconds** — keeps developer feedback loops tight.
- **Use `scope="session"` for clients** — creating one `requests.Session` per test is wasteful; session-scoped fixtures reuse connections.
- **Parallel regression** — `pytest -n auto` uses all cores; keep tests stateless so order doesn't matter.

### Code Quality

- **Type hints everywhere** — every function signature uses type hints; enables IDE autocomplete and mypy checks.
- **Descriptive test names** — `test_create_user_returns_201_with_echoed_payload` beats `test_post_user`.
- **Allure metadata on every test** — `@allure.epic`, `@allure.feature`, `@allure.story`, and `@allure.title` feed the interactive report.

---

## Adding a New Resource

1. **Create the client** → `api_clients/widgets_client.py` (inherit `BaseClient`)
2. **Create the schema** → add `WidgetSchema` in `data/schemas/models.py`
3. **Add fixture** → register `widgets_client` in `conftest.py`
4. **Write smoke test** → `tests/smoke/test_widgets_smoke.py`
5. **Write regression tests** → `tests/regression/test_widgets_crud.py`

That's it — the framework handles logging, retry, auth, reporting, and CI automatically.

## Test Execution

40 Automated API Tests
- Smoke Tests
- CRUD Validation
- Schema Validation
- Response Time Checks

Result:
✅ Passed: 40
❌ Failed: 0
⏱ Duration: 55.85s

---

## License

MIT — see `LICENSE` for details.
