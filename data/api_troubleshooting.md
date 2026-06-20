# API Troubleshooting Guide

## Common API Errors and Solutions

### Error 401: Unauthorized
**Cause:** Invalid or expired API key.

**Solution:**
1. Verify your API key in Dashboard → Settings → API Keys.
2. Check if the key has been revoked or expired.
3. Regenerate a new key if necessary:
   ```
   curl -X POST https://api.acmecloud.io/v2/keys/regenerate \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
   ```
4. Update the key in all services within 60 seconds to avoid downtime.

### Error 403: Forbidden
**Cause:** Insufficient permissions for the requested resource.

**Solution:**
1. Check your account's role assignment in Dashboard → Team → Roles.
2. Required roles per endpoint:
   - `GET /api/v2/data` → Viewer role or above
   - `POST /api/v2/data` → Developer role or above
   - `DELETE /api/v2/data` → Admin role only
3. Contact your organization admin to request elevated permissions.

### Error 429: Rate Limited
**Cause:** Too many requests in a short time window.

**Solution:**
1. Current rate limits by plan:
   - Free: 100 requests/minute
   - Pro: 1,000 requests/minute
   - Enterprise: 10,000 requests/minute
2. Implement exponential backoff in your client code:
   ```python
   import time
   for attempt in range(5):
       response = make_request()
       if response.status_code != 429:
           break
       wait_time = 2 ** attempt
       time.sleep(wait_time)
   ```
3. Use bulk endpoints to reduce total API calls.
4. Consider upgrading your plan for higher limits.

### Error 500: Internal Server Error
**Cause:** An unexpected error occurred on the server.

**Solution:**
1. Retry the request after 30 seconds.
2. Check the Acme Cloud status page: https://status.acmecloud.io
3. If the error persists, contact support with:
   - Request ID (found in the `X-Request-ID` response header)
   - Timestamp of the request
   - Full request payload (redact sensitive data)

### Error 503: Service Unavailable
**Cause:** The service is temporarily unavailable due to maintenance or overload.

**Solution:**
1. Check the status page for scheduled maintenance windows.
2. Implement circuit breaker patterns in your application.
3. Configure failover to a secondary region if available.

## API Timeout Settings

Default timeout values:
- Connection timeout: 10 seconds
- Read timeout: 30 seconds
- Write timeout: 60 seconds

To configure custom timeouts:
```python
import requests
response = requests.get(
    "https://api.acmecloud.io/v2/data",
    timeout=(10, 60)  # (connect, read)
)
```

## Webhook Configuration

To set up webhooks for event notifications:
```bash
acme webhooks create \
  --url https://your-server.com/webhook \
  --events deployment.success,deployment.failure \
  --secret your_webhook_secret
```

Verify webhook signatures:
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```
