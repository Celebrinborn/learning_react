# Authentication & Configuration Guide

This document explains how authentication works in the DND Stats Sheet application, how configuration is structured, and how to run the system in each environment.

**Audience**: Experienced engineers who understand HTTP, JWTs, and containers but are new to practical OAuth / CIAM.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Token Flow](#2-token-flow)
3. [Key Identifiers](#3-key-identifiers)
4. [Dual-Mode Authentication](#4-dual-mode-authentication)
5. [Build-Time vs Runtime Configuration](#5-build-time-vs-runtime-configuration)
6. [Why Config Is Split Across Three Files](#6-why-config-is-split-across-three-files)
7. [Backend Auth Architecture](#7-backend-auth-architecture)
8. [Running in Each Environment](#8-running-in-each-environment)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Architecture Overview

### What is CIAM?

CIAM (Customer Identity and Access Management) is identity management for external users (customers), as opposed to corporate employees. Microsoft Entra External ID is Microsoft's CIAM product. It handles:

- User signup and sign-in (email, social, MFA)
- Password storage and reset
- Token issuance (OAuth 2.0 / OIDC)
- Account lifecycle

The application never stores passwords. Entra External ID owns the user account and credential management entirely.

### The Three Participants

```
 +-----------------------+        +-------------------------+
 |   Entra External ID   |        |     SPA (React)         |
 |   (CIAM / IdP)        |        |     MSAL.js             |
 |                        |        |                         |
 |  - Hosts login page    |<------>|  - Redirects user to    |
 |  - Issues tokens       |        |    Entra for login      |
 |  - Manages accounts    |        |  - Receives tokens      |
 |  - Publishes JWKS      |        |  - Sends access token   |
 +-----------+------------+        |    to API               |
             |                     +------------+------------+
             | JWKS (public keys)               |
             |                                  | Bearer token
             v                                  v
 +-----------------------+        +-------------------------+
 |   API (FastAPI)       |        |   Browser               |
 |                       |        |                         |
 |  - Validates JWT      |<-------|  - User interacts here  |
 |  - Checks signature,  |        |                         |
 |    issuer, audience,   |        +-------------------------+
 |    expiry              |
 |  - Returns user data   |
 +-----------------------+
```

**CIAM (Entra External ID)**: The identity provider. It owns user accounts and issues tokens. The application trusts it because tokens are signed with keys published at a known JWKS endpoint.

**SPA (React frontend)**: Uses MSAL.js to redirect users to Entra for login. After login, MSAL stores tokens and silently refreshes them. On every API call, the SPA attaches the access token as a `Bearer` header.

**API (FastAPI backend)**: Validates JWT access tokens. It never talks to Entra during a normal request -- it only fetches JWKS (public signing keys) to verify token signatures. The JWKS response is cached.

### What MSAL Does

MSAL (Microsoft Authentication Library) is a client-side library that handles the OAuth 2.0 Authorization Code + PKCE flow. It:

1. Builds the authorization URL and redirects the user to Entra
2. Handles the redirect back with the authorization code
3. Exchanges the code for tokens (ID token + access token)
4. Caches tokens in `sessionStorage`
5. Silently refreshes expired access tokens using refresh tokens
6. Provides `acquireTokenSilent()` for getting tokens before API calls

The SPA never sees or handles authorization codes directly. MSAL abstracts the entire OAuth dance.

---

## 2. Token Flow

### Step-by-step: from login to API call

```
1. User clicks "Sign in with Microsoft"
      |
2. SPA calls msalInstance.loginRedirect()
      |
3. Browser redirects to Entra login page
   https://dndportal.ciamlogin.com/{tenant-id}/oauth2/v2.0/authorize
   ?client_id={spa-client-id}
   &redirect_uri=http://localhost:5173/
   &scope=openid profile email api://{api-client-id}/access_as_user
   &response_type=code
   &code_challenge={pkce-challenge}
      |
4. User enters credentials at Entra
      |
5. Entra redirects back to SPA with authorization code
   http://localhost:5173/?code={auth-code}
      |
6. MSAL exchanges code for tokens (automatic, invisible)
   POST https://dndportal.ciamlogin.com/{tenant-id}/oauth2/v2.0/token
      |
7. MSAL receives and caches:
   - ID token (who the user is -- used by SPA only)
   - Access token (what the user can do -- sent to API)
   - Refresh token (used to get new access tokens silently)
      |
8. SPA makes API call:
   GET /me
   Authorization: Bearer {access-token}
      |
9. API validates the access token:
   a. Fetch JWKS from Entra (cached after first call)
   b. Verify RS256 signature against public key
   c. Check "iss" (issuer) matches expected value
   d. Check "aud" (audience) matches API client ID
   e. Check "exp" (expiry) is in the future
      |
10. API returns: { "subject": "user-guid-from-sub-claim" }
```

### ID Token vs Access Token

| Property | ID Token | Access Token |
|----------|----------|--------------|
| Purpose | Proves identity | Grants API access |
| Audience | The SPA (`spa-client-id`) | The API (`api://api-client-id`) |
| Used by | Frontend only | Sent to backend |
| Contains | `name`, `email`, `sub` | `sub`, `scp` (scopes), `aud` |
| Lifetime | ~1 hour | ~1 hour |

The SPA never sends the ID token to the API. The API never needs to know the user's email or display name -- it only needs the `sub` (subject) claim from the access token to identify the user.

---

## 3. Key Identifiers

These are public, non-secret values. They are safe to commit to source control.

| Identifier | Value | Purpose |
|---|---|---|
| CIAM authority host | `dndportal.ciamlogin.com` | Entra tenant login domain |
| Tenant ID | `28a2c50b-b85c-47c4-8dd3-484dfbab055f` | Identifies the CIAM tenant |
| SPA client ID | `cb31ddbc-6b5b-462e-a159-0eee2cd909f6` | App registration for the React SPA |
| API client ID | `f50fed3a-b353-4f4c-b8f5-fb26733d03e5` | App registration for the FastAPI backend |
| API scope | `api://f50fed3a-b353-4f4c-b8f5-fb26733d03e5/access_as_user` | Permission the SPA requests |
| Token issuer | `https://28a2c50b-...484dfbab055f.ciamlogin.com/28a2c50b-...484dfbab055f/v2.0` | `iss` claim in tokens (uses tenant ID as subdomain) |
| JWKS endpoint | `https://dndportal.ciamlogin.com/28a2c50b-...484dfbab055f/discovery/v2.0/keys` | Public signing keys for token verification |

**Important**: The token issuer URL uses the tenant ID as the subdomain (`{tenant-id}.ciamlogin.com`), while the authority, JWKS, and authorization endpoints use the tenant name (`dndportal.ciamlogin.com`). This is a CIAM-specific quirk from Microsoft. The correct issuer comes from the [OpenID Connect discovery document](https://dndportal.ciamlogin.com/28a2c50b-b85c-47c4-8dd3-484dfbab055f/v2.0/.well-known/openid-configuration).

---

## 4. Dual-Mode Authentication

The system supports two auth modes, switched by environment variable.

| Mode | Frontend | Backend | When |
|---|---|---|---|
| `local_fake` | Login form (any credentials), no token sent | Returns hardcoded dev user, no validation | Local development |
| `entra_external_id` | MSAL redirect to Microsoft login, Bearer token on every call | Validates JWT (signature, issuer, audience, expiry) | Production, containers with real auth |

### Switching modes

| Layer | Environment Variable | Default (dev) | Default (prod) |
|---|---|---|---|
| Frontend | `VITE_AUTH_MODE` | `local_fake` | `entra_external_id` |
| Backend | `AUTH_MODE` | `local_fake` | `entra_external_id` |

To test real Entra auth locally, set both:
- `VITE_AUTH_MODE=entra_external_id` (in `src/frontend/.env.local`)
- `AUTH_MODE=entra_external_id` (shell env var or `.env` for backend)

### How `local_fake` works

- **Frontend**: Shows a username/password form. Accepts anything. Stores a mock token in `localStorage`. API calls are made without an `Authorization` header.
- **Backend**: `LocalFakeAuthProvider` returns `UserPrincipal(subject="local-dev-user")` for every request. No token parsing or validation happens.

This mode exists so developers can work without an internet connection or Azure account.

### How `entra_external_id` works

- **Frontend**: MSAL redirects to Entra login page. On success, caches tokens in `sessionStorage`. Before each API call, `acquireTokenSilent()` gets a fresh access token and attaches it as `Authorization: Bearer {token}`.
- **Backend**: `EntraAuthProvider` extracts the Bearer token, verifies the RS256 signature using cached JWKS keys, checks issuer/audience/expiry, and returns `UserPrincipal(subject=claims["sub"])`.

---

## 5. Build-Time vs Runtime Configuration

### Frontend: build-time (Vite)

All frontend configuration is resolved at build time:

1. `VITE_APP_ENV` determines which config block to use (`dev`, `test`, `prod`)
2. `VITE_AUTH_MODE` optionally overrides the auth mode
3. Vite bakes these into the JavaScript bundle via `import.meta.env`
4. The resulting static files have no runtime configuration

This means the **same source code produces different bundles** depending on build-time env vars:
- `npm run start` (local dev) uses `.env.dev` → `local_fake` mode, `localhost` API
- Docker build with `APP_ENV=prod` → `entra_external_id` mode, relative `/api` URL

### Backend: runtime (environment variables)

Backend configuration is loaded at server startup:

1. `APP_ENV` selects the base config (`dev` or `prod`)
2. `AUTH_MODE` optionally overrides auth mode at runtime
3. No rebuild needed to switch configurations

This works because the backend runs in a container with environment variables injected at deploy time.

### Why the difference?

| Concern | Frontend | Backend |
|---|---|---|
| Deployed as | Static files (nginx) | Running process (uvicorn) |
| Can read env vars at runtime? | No (it's JavaScript in a browser) | Yes |
| Config changes require | Rebuild | Restart |

---

## 6. Why Config Is Split Across Three Files

### `src/frontend/src/config/app.config.ts`

**Role**: Single source of truth for all frontend configuration.

Contains environment-specific settings: API base URL, storage container names, auth identifiers (client IDs, tenant ID, authority host, redirect URIs, scopes). Exports `getConfig()` and a `config` singleton.

This file is framework-agnostic -- it knows nothing about MSAL, React, or HTTP.

### `src/frontend/src/config/msalConfig.ts`

**Role**: Adapts auth config into MSAL's type system.

MSAL requires specific object shapes (`Configuration`, `PopupRequest`, `RedirectRequest`). This file translates `app.config` values into those shapes. For example, it computes the MSAL authority URL from separate `entraAuthorityHost` and `entraTenantId` fields:

```typescript
authority: `https://${config.auth.entraAuthorityHost}/${config.auth.entraTenantId}`
```

It also sets MSAL-specific options like `cacheLocation: "sessionStorage"` and `knownAuthorities`.

### `src/frontend/src/config/service.config.ts`

**Role**: Service-layer configuration for API communication + re-exports.

Provides `API_BASE_URL`, `buildApiUrl()`, and `DEFAULT_HEADERS`. Also re-exports `config` and `AUTH_MODE` from `app.config.ts` for backward compatibility -- most consumer files import from `service.config`.

### Why not one file?

Separation of concerns:
- **app.config**: *what* the settings are (data)
- **msalConfig**: *how* MSAL should be configured (MSAL-specific adapter)
- **service.config**: *how* to talk to the API (HTTP-level helpers)

Mixing MSAL types with app-level config would create tight coupling between the auth library and the configuration layer.

---

## 7. Backend Auth Architecture

The backend uses hexagonal architecture: providers implement interfaces, the builder instantiates concrete providers, and routes depend only on abstractions.

```
main.py
  |
  |  At startup:
  |  builder = AppBuilder()                          # reads config
  |  provider = builder.build_auth_provider()        # creates provider
  |  app.dependency_overrides[get_current_user] = provider.dependency()
  |
  v
routes/auth.py
  |
  |  @router.get("/me")
  |  async def me(user = Depends(get_current_user)):
  |      return user
  |
  v
auth/dependencies.py
  |
  |  async def get_current_user(request):
  |      raise HTTPException(401)    # placeholder, overridden at startup
  |
  v
auth/providers/base.py (IAuthProvider protocol)
  |
  |  def dependency() -> Callable  # returns a FastAPI dependency
  |
  +---> auth/providers/local_fake.py
  |       Returns UserPrincipal(subject="local-dev-user")
  |       No token validation
  |
  +---> auth/providers/entra.py
          Validates JWT with PyJWT
          Fetches JWKS from Entra (cached)
          Returns UserPrincipal(subject=claims["sub"])
```

### Key files

| File | Purpose |
|---|---|
| `src/backend/src/auth/models.py` | `UserPrincipal` model (just `subject: str`) |
| `src/backend/src/auth/providers/base.py` | `IAuthProvider` protocol |
| `src/backend/src/auth/providers/entra.py` | JWT validation against Entra JWKS |
| `src/backend/src/auth/providers/local_fake.py` | Hardcoded dev user, no validation |
| `src/backend/src/auth/dependencies.py` | `get_current_user` placeholder dependency |
| `src/backend/src/builder.py` | `AppBuilder.build_auth_provider()` factory |
| `src/backend/src/config.py` | Auth config (issuer, audience, JWKS URL) |
| `src/backend/src/main.py` | Wires auth provider at startup |

### How FastAPI dependency override works

FastAPI's `dependency_overrides` dict replaces a dependency function with another at runtime. The placeholder `get_current_user` (which always returns 401) is replaced at startup with the real provider's dependency. This lets routes be defined independently of which auth provider is active.

---

## 8. Running in Each Environment

### Local development (`npm run start`)

**Frontend**:
```bash
cd src/frontend
npm run start    # alias for npm run dev
```
- Reads `.env.dev` (via Vite config)
- Auth mode: `local_fake` (default)
- API URL: `http://localhost:8000`
- Login form accepts any credentials

**Backend**:
```bash
cd src/backend
# activate venv, then:
python -m uvicorn src.main:app --reload
```
- `APP_ENV` defaults to `dev`
- Auth mode: `local_fake` (default)
- `/me` returns `{"subject": "local-dev-user"}` without any token

**To test real Entra auth locally**:
1. Add to `src/frontend/.env.local`:
   ```
   VITE_AUTH_MODE=entra_external_id
   ```
2. Set backend env var:
   ```
   AUTH_MODE=entra_external_id
   ```
3. Restart both. The frontend will show "Sign in with Microsoft" instead of the form.
4. `http://localhost:5173/` must be registered as a redirect URI in the Entra SPA app registration.

### Local containers (Docker Compose)

```bash
# In VSCode: use the "Run All" task, or:
docker compose -f .devcontainer/docker-compose.yml up
```

- Backend runs on port 8000, frontend on port 5173
- Both default to `APP_ENV=dev` / `local_fake`
- CORS configured for `http://localhost:5173`

To use Entra auth in containers, add to `.devcontainer/docker-compose.yml` backend environment:
```yaml
environment:
  - AUTH_MODE=entra_external_id
```
And set `VITE_AUTH_MODE=entra_external_id` for the frontend.

### Production (Azure Container Apps)

**Frontend build**:
```bash
APP_ENV=prod npm run build
```
- Produces static files with `entra_external_id` mode baked in
- API URL is `/api` (relative, proxied by nginx to backend container)
- Redirect URI is `window.location.origin` (works on any domain)

**Backend**:
- `APP_ENV=prod` set in Dockerfile
- Auth mode: `entra_external_id` (from prod config)
- Validates tokens against Entra JWKS endpoint

**Deployment**: GitHub Actions builds Docker images, pushes to Azure Container Registry, and deploys to Container Apps. See `docs/sensitive/azure-deployment.md` for infrastructure details.

---

## 9. Troubleshooting

### `/me` returns 401 "Auth provider not configured"

The auth provider isn't wired in `main.py`. Check that `app.dependency_overrides[get_current_user]` is set at startup. This should happen automatically via `AppBuilder.build_auth_provider()`.

### MSAL redirect fails or loops

- Check that `entraRedirectUri` in `app.config.ts` matches a redirect URI registered in the Entra portal for the SPA app registration.
- For local dev: `http://localhost:5173/`
- For production: the actual domain origin

### Token validation fails with "Invalid token"

- **Wrong issuer**: The `iss` claim uses `{tenant-id}.ciamlogin.com` (not `dndportal.ciamlogin.com`). Verify `entra_issuer` in `config.py` matches the issuer from the [OIDC discovery document](https://dndportal.ciamlogin.com/28a2c50b-b85c-47c4-8dd3-484dfbab055f/v2.0/.well-known/openid-configuration).
- **Wrong audience**: The `aud` claim must be `api://f50fed3a-b353-4f4c-b8f5-fb26733d03e5`. Check `entra_audience` in config.
- **Expired token**: Tokens last ~1 hour. MSAL should refresh automatically. If not, the user needs to log in again.

### `acquireTokenSilent` fails

This happens when there's no cached token or refresh token. Common causes:
- User logged in with `openid profile email` scopes but not the API scope. Check that `loginRequest` in `msalConfig.ts` or the login call includes the API scope.
- Session storage was cleared (new tab, browser restart).

### CORS errors on API calls

Check that `CORS_ORIGINS` in the backend includes the frontend origin:
- Local: `http://localhost:5173`
- Docker: `http://localhost:5173,http://frontend:5173`
- Prod: the actual frontend domain

### Local fake mode doesn't work

- Verify both frontend (`VITE_AUTH_MODE`) and backend (`AUTH_MODE`) are set to `local_fake` (or unset, which defaults to `local_fake` in dev).
- The frontend sends no `Authorization` header in this mode. If the backend is in `entra_external_id` mode, it will reject requests.
