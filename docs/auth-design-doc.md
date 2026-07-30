# Authentication & Authorization Design Document

## Overview

This document describes the authentication and authorization architecture for the DND Stats Sheet application.

| Strategy | Environment | Description |
|----------|-------------|-------------|
| `entra_external_id` | dev/test/prod | Real login via Microsoft Entra External ID (OIDC/JWT) |

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
    subject: str              # Stable user ID (Entra `sub` claim)
    username: str | None      # User-chosen username (None if not yet registered)
    roles: list[str]          # e.g., ["admin"], ["editor"], ["viewer"]
    auth_scheme: Literal["entra_external_id"]
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
│   └── providers/
│       ├── __init__.py
│       ├── base.py              # AuthProvider protocol/interface
│       └── entra.py             # EntraAuthProvider
├── models/
│   └── user.py                  # AppUser model (stored users)
├── storage/
│   └── user.py                  # UserStorage interface + implementation
├── routes/
│   └── auth.py                  # /me, /register endpoints
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

## 4. Authentication: `entra_external_id`

### 4.1 Purpose

- Real signup/sign-in for arbitrary emails via Entra External ID user flows
- Frontend obtains access token via MSAL
- Backend validates JWT and maps claims to `UserPrincipal`

### 4.2 Frontend Token Acquisition

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

### 4.3 Backend JWT Validation

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

### 4.4 Authentication + User Lookup Flow

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

### 4.5 Configuration

**Note**: Configuration is now stored in `config.py` (backend) and `service.config.ts` (frontend), not in environment variables. The settings below are defined per-environment in those files.

**Backend Config** (`src/backend/src/config.py`):

```python
# Auth settings
auth_mode: "entra_external_id"
entra_issuer: "https://<tenant>.ciamlogin.com/<tenant-id>/v2.0"
entra_audience: "api://<api-client-id>"
entra_jwks_url: "https://<tenant>.ciamlogin.com/<tenant-id>/discovery/v2.0/keys"
entra_required_scopes: "api://<api-client-id>/access_as_user"

# Azure Blob Storage (uses Managed Identity, no connection string)
azure_storage_account_url: "https://<storage-account>.blob.core.windows.net"
azure_container_maps: "maps"
azure_container_characters: "characters"
azure_container_users: "users"
```

**Frontend Config** (`src/frontend/src/config/service.config.ts`):

```typescript
authMode: 'entra_external_id'
entraClientId: '<spa-client-id>'
entraAuthority: 'https://<tenant>.ciamlogin.com/<tenant-id>'
apiScope: 'api://<api-client-id>/access_as_user'
apiBaseUrl: 'https://api.example.com'
```

---

## 5. Strategy Selection

### 5.1 Single Switch Point

Backend reads environment at startup:

```python
# config/settings.py
ENV: Literal["dev", "test", "prod"] = os.getenv("APP_ENV", "dev")
AUTH_MODE: Literal["entra_external_id"] = os.getenv("AUTH_MODE", "entra_external_id")
```

### 5.2 Provider Factory

```python
# builder.py
def build_auth_provider() -> AuthProvider:
    if settings.AUTH_MODE == "entra_external_id":
        return EntraAuthProvider(
            issuer=settings.ENTRA_ISSUER,
            audience=settings.ENTRA_AUDIENCE,
            jwks_url=settings.ENTRA_JWKS_URL,
        )
    else:
        raise ValueError(f"Unknown AUTH_MODE: {settings.AUTH_MODE}")
```

---

## 6. API Endpoints

### 6.1 Auth Endpoints

| Endpoint | Auth Required | Description |
|----------|---------------|--------------|
| `GET /me` | Yes | Returns current `UserPrincipal` |
| `POST /auth/register` | Yes | Register username (new users only) |

### 6.2 Admin Endpoints

| Endpoint | Auth Required | Role | Description |
|----------|---------------|------|-------------|
| `GET /admin/users` | Yes | admin | List all users |
| `POST /admin/ban` | Yes | admin | Ban a user by subject |
| `POST /admin/unban` | Yes | admin | Unban a user by subject |

### 6.3 Protected Endpoints

| Endpoint | Auth Required | Description |
|----------|---------------|-------------|
| `GET /api/*` | Yes | All API routes |

### 6.4 Public Endpoints

| Endpoint | Auth Required | Description |
|----------|---------------|-------------|
| `GET /health` | No | Health check |

---

## 7. Error Responses

| Status | Condition |
|--------|-----------|
| 401 Unauthorized | Missing or invalid credentials |
| 403 Forbidden | Valid credentials but insufficient role, or banned |
| 409 Conflict | Username already taken (registration) |

---

## 8. Implementation Checklist

### Backend

- [ ] Create `UserPrincipal` model in `src/auth/models.py`
- [ ] Create `AppUser` model in `src/models/user.py`
- [ ] Create `AuthProvider` protocol in `src/auth/providers/base.py`
- [ ] Implement `EntraAuthProvider` in `src/auth/providers/entra.py`
- [ ] Create `UserStorage` interface and implementation
- [ ] Create `get_current_user` dependency in `src/auth/dependencies.py`
- [ ] Create `require_role`, `has_role` in `src/auth/authorization.py`
- [ ] Add `/me` endpoint in `src/routes/auth.py`
- [ ] Add `/auth/register` endpoint
- [ ] Add `/admin/*` endpoints for user management
- [ ] Add auth config to `src/config/`
- [ ] Wire up in `builder.py`

### Frontend

- [ ] Add MSAL configuration for Entra auth
- [ ] Create auth context/provider
- [ ] Create username registration page
- [ ] Add Bearer token header for API calls
- [ ] Create `/me` display component
- [ ] Add registration redirect logic

### Testing

- [ ] Unit tests for `UserPrincipal` model
- [ ] Unit tests for `AppUser` model
- [ ] Unit tests for authorization helpers
- [ ] Unit tests for username validation
- [ ] Integration tests for registration flow
- [ ] Integration tests for JWT validation (mocked)
- [ ] Integration tests for ban/unban

---

## 9. Security Considerations

1. **JWT validation**: Full validation chain (signature, issuer, audience, expiry)
2. **JWKS caching**: Prevents DoS via key fetching
3. **Role-based access**: All authorization through `UserPrincipal.roles`
4. **No token storage in frontend**: MSAL handles token lifecycle
5. **Username validation**: Prevent reserved words, enforce format
6. **Ban check on every request**: Banned users rejected immediately

---

## 10. Future Considerations

- Refresh token handling
- Session management/revocation
- Audit logging for auth events
- Rate limiting on auth endpoints
- Username change feature
- User profile (avatar, bio, etc.)
