# Authentication & Authorization Design Document

## Overview

This document describes the authentication and authorization architecture for the DND Stats Sheet application. The system supports two auth strategies:

| Strategy | Environment | Description |
|----------|-------------|-------------|
| `local_fake` | dev only | User picks from fake accounts via cookie-based selection |
| `entra_external_id` | test/prod | Real login via Microsoft Entra External ID (OIDC/JWT) |

**Key Design Goal**: Everything outside the auth module sees the same `UserPrincipal` regardless of which strategy is active.

---

## 1. Core Concepts

### 1.1 UserPrincipal Model

A single Pydantic model representing the authenticated user. All application code works with this type only.

**Location**: `src/backend/src/auth/models.py`

```python
from pydantic import BaseModel
from typing import Literal

class UserPrincipal(BaseModel):
    subject: str              # Stable user ID (Entra `sub` claim / fake key in dev)
    username: str | None      # User-chosen username (None if not yet registered)
    roles: list[str]          # e.g., ["admin"], ["editor"], ["viewer"]
    auth_scheme: Literal["local_fake", "entra_external_id"]
```

**Design Decision**: No `email` or `display_name`. Users are identified by:
- `subject` — immutable GUID from Entra (used as FK in data models)
- `username` — human-friendly identifier chosen by user

### 1.2 AppUser Model (Stored in Database)

Since usernames are user-chosen, we need a users table:

**Location**: `src/backend/src/models/user.py`

```python
from pydantic import BaseModel
from datetime import datetime

class AppUser(BaseModel):
    subject: str              # PK - from Entra sub claim
    username: str             # Unique, user-chosen, 3-20 chars, alphanumeric + underscore
    roles: list[str]          # App-level roles (can differ from Entra roles)
    created_at: datetime
    is_banned: bool = False
    banned_at: datetime | None = None
    ban_reason: str | None = None
```

### 1.3 Auth Dependency

All protected routes depend on a single function:

```python
async def get_current_user(request: Request) -> UserPrincipal:
    ...
```

**No other code reads cookies, headers, or JWTs directly.**

### 1.3 Authorization Helpers

Authorization is separate from authentication. Helpers use only `UserPrincipal.roles`:

```python
def require_role(user: UserPrincipal, role: str) -> None:
    """Raises HTTPException 403 if user lacks the required role."""
    
def has_role(user: UserPrincipal, role: str) -> bool:
    """Returns True if user has the specified role."""
```

---

## 2. Module Structure

```
src/backend/src/
├── auth/
│   ├── __init__.py              # Exports: get_current_user, require_role, has_role, UserPrincipal
│   ├── models.py                # UserPrincipal definition
│   ├── dependencies.py          # get_current_user dependency
│   ├── authorization.py         # require_role, has_role helpers
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py              # AuthProvider protocol/interface
│   │   ├── local_fake.py        # LocalFakeAuthProvider
│   │   └── entra.py             # EntraAuthProvider
│   └── dev_users.json           # Fake user data (dev only)
├── models/
│   └── user.py                  # AppUser model (stored users)
├── storage/
│   └── user.py                  # UserStorage interface + implementation
├── routes/
│   ├── auth.py                  # /me, /register endpoints
│   └── dev_auth.py              # /dev/* endpoints (dev only)
```

---

## 3. User Registration Flow

### 3.1 New User Flow (Entra)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User logs   │────▶│  Validate    │────▶│  Lookup by   │────▶│  Return      │
│  in via MSAL │     │  JWT token   │     │  subject     │     │  UserPrincipal│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                          Not found?
                                                 ▼
                                    ┌──────────────────────┐
                                    │  username = None     │
                                    │  Frontend redirects  │
                                    │  to /register page   │
                                    └──────────────────────┘
```

### 3.2 Registration Endpoint

```http
POST /auth/register
Authorization: Bearer <token>
Content-Type: application/json

{ "username": "chosen_username" }
```

**Validation**:
- 3-20 characters
- Alphanumeric + underscore only
- Case-insensitive uniqueness check
- Not on reserved list (admin, root, system, etc.)

**Response**:
- 201: User created, returns `UserPrincipal`
- 400: Invalid username format
- 409: Username already taken

### 3.3 Frontend Registration Flow

```typescript
// After login, check if user needs to register
const user = await fetch('/me').then(r => r.json());

if (user.username === null) {
  // Redirect to username selection page
  navigate('/register');
}
```

---

## 4. Strategy A: `local_fake` (Dev Only)

### 4.1 Purpose

- Fast local development without external dependencies
- No OIDC, no tokens
- User "logs in" by selecting a fake account

### 4.2 Fake User Data

**File**: `src/backend/src/auth/dev_users.json`

```json
{
  "admin": {
    "subject": "dev-admin-001",
    "username": "dev_admin",
    "roles": ["admin", "editor", "viewer"]
  },
  "editor": {
    "subject": "dev-editor-001",
    "username": "dev_editor",
    "roles": ["editor", "viewer"]
  },
  "viewer": {
    "subject": "dev-viewer-001",
    "username": "dev_viewer",
    "roles": ["viewer"]
  },
  "new_user": {
    "subject": "dev-new-001",
    "username": null,
    "roles": ["viewer"]
  }
}
```

Note: `new_user` has `username: null` to test the registration flow in dev.

### 4.3 Dev-Only Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dev/select-user` | POST | Sets `dev_user` cookie |
| `/dev/logout` | POST | Clears `dev_user` cookie |
| `/dev/users` | GET | Returns list of available fake users |

**Request/Response**:

```http
POST /dev/select-user
Content-Type: application/json

{ "user_key": "admin" }
```

**Cookie Settings**:
- Name: `dev_user`
- Value: selected `user_key`
- `HttpOnly=true`
- `SameSite=Lax`
- `Secure=false` (localhost)

### 4.4 Request Authentication Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Read Cookie    │────▶│  Lookup in       │────▶│  Build            │
│  `dev_user`     │     │  dev_users.json  │     │  UserPrincipal    │
└─────────────────┘     └──────────────────┘     └───────────────────┘
        │                       │
        ▼                       ▼
   Missing: 401           Unknown: 401
```

### 4.5 Safety Guardrails (Non-Negotiable)

On backend startup:

```python
if auth_mode == "local_fake" and env != "dev":
    raise RuntimeError(
        "FATAL: local_fake auth is only allowed in dev environment. "
        f"Current ENV={env}. Refusing to start."
    )
```

Optional additional check:
```python
if env == "dev" and host not in ("127.0.0.1", "localhost", "0.0.0.0"):
    raise RuntimeError("Dev server must bind to localhost only")
```

### 4.6 Frontend Behavior (Dev)

When `VITE_AUTH_MODE=local_fake`:

1. Show "Dev User" selector dropdown in UI
2. On selection change: `POST /dev/select-user` with `{ credentials: "include" }`
3. Refresh `/me` to display current identity
4. All API calls use `credentials: "include"` for cookie flow

---

## 5. Strategy B: `entra_external_id` (Test/Prod)

### 5.1 Purpose

- Real signup/sign-in for arbitrary emails via Entra External ID user flows
- Frontend obtains access token via MSAL
- Backend validates JWT and maps claims to `UserPrincipal`

### 5.2 Frontend Token Acquisition

Using MSAL.js:

```typescript
const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID,
    authority: import.meta.env.VITE_ENTRA_AUTHORITY,
    redirectUri: window.location.origin,
  }
};

// Acquire token for API scope
const tokenResponse = await msalInstance.acquireTokenSilent({
  scopes: [import.meta.env.VITE_API_SCOPE]
});

// Call backend with Bearer token
fetch('/api/me', {
  headers: {
    'Authorization': `Bearer ${tokenResponse.accessToken}`
  }
});
```

### 5.3 Backend JWT Validation

**Required Validations**:

| Check | Description |
|-------|-------------|
| Signature | Verify against issuer's JWKS |
| `iss` | Must match Entra External ID authority |
| `aud` | Must match API app registration |
| `exp` | Token not expired |
| `nbf` | Token is active (if present) |

**Implementation Notes**:
- Cache JWKS (do not fetch per request)
- Return **401 Unauthorized** for missing/invalid tokens

### 5.4 Authentication + User Lookup Flow

```python
async def get_current_user(request: Request) -> UserPrincipal:
    # 1. Validate JWT, extract subject
    claims = await validate_jwt(request)
    subject = claims["sub"]
    
    # 2. Lookup user in database
    app_user = await user_storage.get_by_subject(subject)
    
    # 3. Check if banned
    if app_user and app_user.is_banned:
        raise HTTPException(status_code=403, detail="Account suspended")
    
    # 4. Build UserPrincipal
    return UserPrincipal(
        subject=subject,
        username=app_user.username if app_user else None,
        roles=app_user.roles if app_user else ["viewer"],  # default role for new users
        auth_scheme="entra_external_id"
    )
```

### 5.5 Configuration

**Backend Environment Variables**:

```env
# Auth
AUTH_MODE=entra_external_id
ENTRA_ISSUER=https://<tenant>.ciamlogin.com/<tenant-id>/v2.0
ENTRA_AUDIENCE=api://<api-client-id>
ENTRA_JWKS_URL=https://<tenant>.ciamlogin.com/<tenant-id>/discovery/v2.0/keys
# Optional
ENTRA_REQUIRED_SCOPES=api://<api-client-id>/access_as_user

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
AZURE_BLOB_CONTAINER_MAPS=maps
AZURE_BLOB_CONTAINER_CHARACTERS=characters
AZURE_BLOB_CONTAINER_USERS=users
```

**Frontend Environment Variables**:

```env
VITE_AUTH_MODE=entra_external_id
VITE_ENTRA_CLIENT_ID=<spa-client-id>
VITE_ENTRA_AUTHORITY=https://<tenant>.ciamlogin.com/<tenant-id>
VITE_API_SCOPE=api://<api-client-id>/access_as_user
VITE_API_BASE_URL=https://api.example.com
```

---

## 6. Strategy Selection

### 6.1 Single Switch Point

Backend reads environment at startup:

```python
# config/settings.py
ENV: Literal["dev", "test", "prod"] = os.getenv("APP_ENV", "dev")
AUTH_MODE: Literal["local_fake", "entra_external_id"] = os.getenv("AUTH_MODE", "local_fake")
```

### 6.2 Provider Factory

```python
# builder.py
def build_auth_provider() -> AuthProvider:
    if settings.AUTH_MODE == "local_fake":
        if settings.ENV != "dev":
            raise RuntimeError("local_fake auth only allowed in dev")
        return LocalFakeAuthProvider()
    elif settings.AUTH_MODE == "entra_external_id":
        return EntraAuthProvider(
            issuer=settings.ENTRA_ISSUER,
            audience=settings.ENTRA_AUDIENCE,
            jwks_url=settings.ENTRA_JWKS_URL,
        )
    else:
        raise ValueError(f"Unknown AUTH_MODE: {settings.AUTH_MODE}")
```

### 6.3 No Mixed Mode

**Never** support "sometimes fake, sometimes real" in the same environment:

| Environment | Auth Mode |
|-------------|-----------|
| dev | `local_fake` |
| test | `entra_external_id` |
| prod | `entra_external_id` |

---

## 7. API Endpoints

### 7.1 Auth Endpoints

| Endpoint | Auth Required | Description |
|----------|---------------|-------------|
| `GET /me` | Yes | Returns current `UserPrincipal` |
| `POST /auth/register` | Yes | Register username (new users only) |

### 7.2 Admin Endpoints

| Endpoint | Auth Required | Role | Description |
|----------|---------------|------|-------------|
| `GET /admin/users` | Yes | admin | List all users |
| `POST /admin/ban` | Yes | admin | Ban a user by subject |
| `POST /admin/unban` | Yes | admin | Unban a user by subject |

### 7.3 Protected Endpoints

| Endpoint | Auth Required | Description |
|----------|---------------|-------------|
| `GET /api/*` | Yes | All API routes |

### 7.4 Public Endpoints

| Endpoint | Auth Required | Description |
|----------|---------------|-------------|
| `GET /health` | No | Health check |

### 7.5 Dev-Only Endpoints

| Endpoint | Condition | Description |
|----------|-----------|-------------|
| `POST /dev/select-user` | `ENV=dev` AND `AUTH_MODE=local_fake` | Select fake user |
| `POST /dev/logout` | `ENV=dev` AND `AUTH_MODE=local_fake` | Clear session |
| `GET /dev/users` | `ENV=dev` AND `AUTH_MODE=local_fake` | List fake users |

**These endpoints must not be registered when not in dev mode.**

---

## 8. Error Responses

| Status | Condition |
|--------|-----------|
| 401 Unauthorized | Missing or invalid credentials |
| 403 Forbidden | Valid credentials but insufficient role, or banned |
| 409 Conflict | Username already taken (registration) |

---

## 9. Implementation Checklist

### Backend

- [ ] Create `UserPrincipal` model in `src/auth/models.py`
- [ ] Create `AppUser` model in `src/models/user.py`
- [ ] Create `AuthProvider` protocol in `src/auth/providers/base.py`
- [ ] Implement `LocalFakeAuthProvider` in `src/auth/providers/local_fake.py`
- [ ] Implement `EntraAuthProvider` in `src/auth/providers/entra.py`
- [ ] Create `UserStorage` interface and implementation
- [ ] Create `get_current_user` dependency in `src/auth/dependencies.py`
- [ ] Create `require_role`, `has_role` in `src/auth/authorization.py`
- [ ] Add `/me` endpoint in `src/routes/auth.py`
- [ ] Add `/auth/register` endpoint
- [ ] Add `/admin/*` endpoints for user management
- [ ] Add `/dev/*` endpoints in `src/routes/dev_auth.py`
- [ ] Add auth config to `src/config/`
- [ ] Wire up in `builder.py`
- [ ] Add startup guardrail check
- [ ] Create `dev_users.json`

### Frontend

- [ ] Add MSAL configuration for Entra auth
- [ ] Create auth context/provider
- [ ] Implement dev user selector component
- [ ] Create username registration page
- [ ] Configure `credentials: "include"` for dev mode
- [ ] Add Bearer token header for Entra mode
- [ ] Create `/me` display component
- [ ] Add registration redirect logic

### Testing

- [ ] Unit tests for `UserPrincipal` model
- [ ] Unit tests for `AppUser` model
- [ ] Unit tests for authorization helpers
- [ ] Unit tests for username validation
- [ ] Integration tests for dev auth flow
- [ ] Integration tests for registration flow
- [ ] Integration tests for JWT validation (mocked)
- [ ] Integration tests for ban/unban

---

## 10. Security Considerations

1. **Dev auth cannot leak to prod**: Hard crash on startup if misconfigured
2. **HttpOnly cookies**: Prevents XSS from reading dev session
3. **JWT validation**: Full validation chain (signature, issuer, audience, expiry)
4. **JWKS caching**: Prevents DoS via key fetching
5. **Role-based access**: All authorization through `UserPrincipal.roles`
6. **No token storage in frontend**: MSAL handles token lifecycle
7. **Username validation**: Prevent reserved words, enforce format
8. **Ban check on every request**: Banned users rejected immediately

---

## 11. Future Considerations

- Refresh token handling
- Session management/revocation
- Audit logging for auth events
- Rate limiting on auth endpoints
- Username change feature
- User profile (avatar, bio, etc.)
