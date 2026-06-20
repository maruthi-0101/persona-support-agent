# API Authentication Guide

## Overview

Acme Cloud Platform uses token-based authentication for all API endpoints. This guide covers the authentication methods, token management, and security best practices.

## Authentication Methods

### 1. API Key Authentication

API keys are the simplest way to authenticate. Suitable for server-to-server communication.

**Generate an API Key:**
1. Go to Dashboard → Settings → API Keys
2. Click "Create New Key"
3. Select the permission scope (read-only, read-write, or admin)
4. Copy the key — it will only be shown once

**Usage:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.acmecloud.io/v2/apps
```

```python
import requests

headers = {"Authorization": "Bearer YOUR_API_KEY"}
response = requests.get("https://api.acmecloud.io/v2/apps", headers=headers)
```

### 2. OAuth 2.0

For applications that act on behalf of users. Supports Authorization Code and Client Credentials flows.

**Authorization Code Flow:**
```
GET https://auth.acmecloud.io/oauth/authorize?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  response_type=code&
  scope=read write
```

**Exchange Code for Token:**
```bash
curl -X POST https://auth.acmecloud.io/oauth/token \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
}
```

### 3. Service Account Tokens

For automated workflows and CI/CD pipelines. Service accounts have long-lived tokens.

**Create a Service Account:**
```bash
acme service-accounts create \
  --name "CI/CD Pipeline" \
  --role developer \
  --description "GitHub Actions deployment"
```

**Token Rotation:**
```bash
acme service-accounts rotate-token --name "CI/CD Pipeline"
```

## Token Scopes

| Scope     | Permissions                                    |
|-----------|------------------------------------------------|
| `read`    | View apps, configs, logs                       |
| `write`   | Deploy, update configs, manage scaling         |
| `admin`   | Manage team members, billing, delete apps      |
| `audit`   | View audit logs and security events            |

## Token Expiration

- API Keys: Never expire (until manually revoked)
- OAuth Access Tokens: Expire after 1 hour
- OAuth Refresh Tokens: Expire after 30 days
- Service Account Tokens: Expire after 90 days (configurable)

## Security Best Practices

1. **Never expose API keys in client-side code** — use environment variables or a secrets manager.
2. **Rotate keys regularly** — set up quarterly key rotation schedules.
3. **Use the minimum required scope** — follow the principle of least privilege.
4. **Enable IP allowlisting** — restrict API access to known IP addresses:
   ```bash
   acme api-keys update KEY_ID --allowed-ips "203.0.113.0/24,198.51.100.42"
   ```
5. **Monitor API key usage** — review access logs weekly:
   ```bash
   acme audit-logs list --filter "action=api.access" --since 7d
   ```
6. **Enable MFA** — required for all admin-level operations.

## Revoking Access

To revoke an API key immediately:
```bash
acme api-keys revoke KEY_ID
```

To revoke all tokens for a user:
```bash
acme users revoke-tokens --email user@example.com
```

**Note:** Revoked tokens are invalidated within 60 seconds across all regions.
