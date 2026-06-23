# Ailovanta Deployment

Ailovanta is still a local MVP. Use local deployment first.

Repository:

```bash
git clone https://github.com/ZqiEE/ailovanta.git
```

## Local API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Open:

```text
API docs:  http://127.0.0.1:8000/docs
App:       http://127.0.0.1:8000/app
Dashboard: http://127.0.0.1:8000/dashboard
```

## Docker

```bash
docker build -t ailovanta .
docker run --rm -p 8000:8000 -v "$PWD/runtime_data:/app/runtime_data" ailovanta
```

Open:

```text
http://127.0.0.1:8000/app
http://127.0.0.1:8000/dashboard
```

## Docker Compose

```bash
docker compose up --build
```

## Node client

```bash
python node_client/client.py --api-url http://127.0.0.1:8000 --contribution 30
```

## Smoke test

After the API is running:

```bash
python scripts/smoke_api.py --api-url http://127.0.0.1:8000
```

## Production gaps

Before a public deployment, add:

- Authentication
- TLS
- Rate limits
- Signed jobs
- Sandboxed workers
- Database migration strategy
- Observability
- Abuse prevention
