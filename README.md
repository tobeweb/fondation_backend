# Fondation Backend (Serverless)

This repository contains the serverless backend for **Optical Center Foundation**.
The stack is built in Python   3.11 on AWS Lambda, orchestrated with the Serverless Framework. It exposes a secured REST API (Amazon API Gateway + Cognito) and persists data in an **Aurora (MySQL) Serverless-v2** cluster.

---

## Contents

* `serverless.yml` – Infrastructure-as-Code that defines functions, API routes, Cognito authoriser and RDS cluster.
* `src/` – Python application code
  * `clients/` – Client onboarding & management
  * `queue/`   – On-site queue management
  * `orders/`  – Order management
  * `db/`      – SQLAlchemy database helpers
  * `utils/`    – Reusable utility helpers (HTTP responses, etc.)
* `tests/` – Unit tests (pytest)
* `requirements.txt` – Python dependencies

---

## Prerequisites

1. **Node ≥ 18** (for the Serverless CLI)
2. **Python 3.11** with a virtual-env manager
3. **AWS CLI v2** configured with credentials that can deploy the stack
4. **Docker** (optional, speeds up packaging on non-linux hosts)

---

## Local Development

```bash
# 1. Clone & install python deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Install serverless & plugins
npm i -g serverless

# 3. Create a .env file with local vars
cp .env.example .env

# 4. Start the API locally (http://localhost:3000)
sls offline start
```

### Calling a function locally

```bash
curl -X POST http://localhost:3000/dev/client \
     -H 'Content-Type: application/json' \
     -d '{"first_name":"John","last_name":"Doe"}'
```

> **Note**: When `serverless-offline` is running, Cognito authentication is skipped automatically.

---

## Deployment

```bash
# Deploy to the dev stage
aws sso login                          # if using AWS SSO
sls deploy --stage dev                 # → https://<apiId>.execute-api.<region>.amazonaws.com/dev

# Promote to production
sls deploy --stage prod
```

The `--stage` flag controls:
* Separate Lambda aliases & API Gateway stages
* Distinct Aurora clusters (dev / prod)
* Distinct Cognito User Pools

---

## Working with the Database (Aurora Serverless v2)

The Aurora cluster is **not** publicly accessible. To open a secure session you can use **AWS Systems Manager Session Manager** (SSM) port forwarding.

```bash
# Substitute <cluster-id> and the generated instance ID
INSTANCE_ID=$(aws rds describe-db-instances --query 'DBInstances[?DBClusterIdentifier==`fondation-back-dev-cluster`].DBInstanceIdentifier' --output text)

aws ssm start-session \
  --target "$INSTANCE_ID" \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["3306"],"localPortNumber":["13306"]}'
```

You can then connect locally via:

```
mysql -h 127.0.0.1 -P 13306 -u admin -p
```

The application obtains an **IAM database authentication token** at runtime; your personal SQL client can do the same:

```bash
mysql --enable-cleartext-plugin -h <cluster-endpoint> -u admin \
  --password="$(aws rds generate-db-auth-token --hostname <cluster-endpoint> --port 3306 --region <region> --username admin)"
```

---

## Running Tests

```bash
pytest -q
```

Tests use **SQLite in-memory** to avoid the need for a live Aurora connection.

---

## Security & Best Practices

* **Least Privilege** IAM roles per function
* API secured with **Cognito User Pools**
* Secrets & connection strings resolved from **SSM Parameter Store**
* **SQLAlchemy** prevents SQL-injection via parameterised queries
* Code formatted with **black** & linted with **ruff** (optional)

---

## Contributing

1. Create a feature branch
2. Add / update unit tests
3. Run linting + tests (`make check` coming soon)
4. Open a PR 🎉

---

© 2024 Optical Center Foundation – All rights reserved. # fondation_backend
