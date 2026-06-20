# Database Integration Guide

## Supported Databases

Acme Cloud Platform provides managed database add-ons for the following database engines:

| Database       | Versions Supported | Add-on Name     |
|----------------|-------------------|-----------------|
| PostgreSQL     | 14, 15, 16       | `postgres`      |
| MySQL          | 8.0, 8.4         | `mysql`         |
| MongoDB        | 6.0, 7.0         | `mongodb`       |
| Redis          | 7.0, 7.2         | `redis`         |
| Elasticsearch  | 8.12, 8.14       | `elasticsearch` |

## Provisioning a Database

### Via CLI

```bash
# Create a PostgreSQL database
acme addons create postgres --plan standard --app my-app

# Create a Redis cache
acme addons create redis --plan premium --app my-app

# List all add-ons for an app
acme addons list --app my-app
```

### Available Plans

**PostgreSQL / MySQL:**
- `hobby`: 64 MB RAM, 1 GB storage, shared CPU — $0/month
- `standard`: 1 GB RAM, 10 GB storage, 1 vCPU — $15/month
- `premium`: 4 GB RAM, 50 GB storage, 2 vCPU — $50/month
- `enterprise`: 16 GB RAM, 200 GB storage, 4 vCPU — $200/month

**Redis:**
- `hobby`: 25 MB — $0/month
- `standard`: 100 MB — $10/month
- `premium`: 1 GB — $30/month

## Connection Configuration

When you provision a database, the connection URL is automatically injected as an environment variable:

- PostgreSQL: `DATABASE_URL`
- MySQL: `MYSQL_URL`
- MongoDB: `MONGODB_URI`
- Redis: `REDIS_URL`

### Python Example (PostgreSQL)

```python
import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
conn.close()
```

### Python Example (Redis)

```python
import os
import redis

REDIS_URL = os.environ["REDIS_URL"]
r = redis.from_url(REDIS_URL)
r.set("key", "value")
print(r.get("key"))
```

## Connection Pooling

For high-traffic applications, enable connection pooling:

```bash
acme addons update postgres --connection-pooling --pool-size 20 --app my-app
```

Recommended pool sizes:
- Low traffic (< 100 req/s): 5-10 connections
- Medium traffic (100-500 req/s): 10-20 connections
- High traffic (> 500 req/s): 20-50 connections

## Backups

Automatic backups are included with all paid plans:
- **Daily backups**: Retained for 7 days (standard), 30 days (premium/enterprise)
- **Point-in-time recovery**: Available on premium and enterprise plans
- **Manual backups**: Create on-demand snapshots

```bash
# Create a manual backup
acme addons backup create --addon postgres-abc123

# List backups
acme addons backup list --addon postgres-abc123

# Restore from backup
acme addons backup restore --addon postgres-abc123 --backup-id bak-xyz789
```

## Migrations

To run database migrations during deployment:

```bash
# Add a release command to your Procfile
release: python manage.py migrate
```

Or run migrations manually:

```bash
acme run --app my-app -- python manage.py migrate
```

## Troubleshooting

### Connection Refused
1. Verify the database add-on is active: `acme addons info postgres-abc123`
2. Check if the app's IP is allowed in the database firewall rules
3. Ensure the `DATABASE_URL` environment variable is set correctly

### Slow Queries
1. Enable query logging: `acme addons update postgres --log-slow-queries --app my-app`
2. Check for missing indexes using `EXPLAIN ANALYZE` on slow queries
3. Review connection pool utilization: `acme addons metrics --addon postgres-abc123`

### Storage Full
1. Check current usage: `acme addons info postgres-abc123`
2. Clean up unused data or old logs
3. Upgrade to a larger plan: `acme addons update postgres --plan premium --app my-app`
