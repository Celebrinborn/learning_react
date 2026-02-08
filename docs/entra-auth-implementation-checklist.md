# Entra Authentication Implementation Checklist

Add real Microsoft Entra External ID authentication alongside the existing stub. Core auth only (login/logout, token validation).

**Approach:** Test-Driven Development (Red-Green) - write tests first, tests focus on observable behavior at the edges, no testing of internal implementation details.

**Key Decisions:**
- Keep both `local_fake` and `entra_external_id` modes (switch via env var)
- Azure app registration is already configured with localhost redirect

---

## Phase 1: Backend Auth

### RED: Write integration tests for /me endpoint
- [ ] Create `src/backend/tests/integration/test_auth_routes.py`
- [ ] Test: `GET /me` returns 401 when no token provided
- [ ] Test: `GET /me` returns 401 when invalid token provided
- [ ] Test: `GET /me` returns 200 with user info when valid token provided (response includes `subject`)
- [ ] Test: existing routes still work without auth (e.g. `GET /health` returns 200)
- [ ] Run tests, confirm they fail (RED)

### GREEN: Implement backend auth
- [ ] Install dependencies: `python-jose[cryptography]`, `httpx` (add to `requirements.txt`)
- [ ] Create `src/backend/src/auth/__init__.py`
- [ ] Create `src/backend/src/auth/models.py` - UserPrincipal model (`subject`, `auth_scheme`)
- [ ] Create `src/backend/src/auth/providers/__init__.py`
- [ ] Create `src/backend/src/auth/providers/base.py` - AuthProvider protocol
- [ ] Create `src/backend/src/auth/providers/entra.py` - JWT validation against Entra JWKS
- [ ] Create `src/backend/src/auth/dependencies.py` - `get_current_user` FastAPI dependency
- [ ] Create `src/backend/src/routes/auth.py` - `GET /me` endpoint
- [ ] Update `src/backend/src/builder.py` - auth provider factory based on config
- [ ] Update `src/backend/src/main.py` - register auth routes
- [ ] Update `src/backend/src/config.py` - fill in Entra values for prod
- [ ] Run tests, confirm they pass (GREEN)

---

## Phase 2: Frontend Auth

### RED: Write Login page tests
- [ ] Create `src/frontend/src/test/Login.test.tsx`
- [ ] Test: in `local_fake` mode, shows username and password fields
- [ ] Test: in `local_fake` mode, submits form and redirects on success
- [ ] Test: in `entra_external_id` mode, shows "Sign in with Microsoft" button
- [ ] Test: in `entra_external_id` mode, does not show username/password fields
- [ ] Run tests, confirm they fail (RED)

### GREEN: Install MSAL and implement Login page
- [ ] Install MSAL: `npm install @azure/msal-browser @azure/msal-react`
- [ ] Create `src/frontend/src/auth/msalConfig.ts` - MSAL configuration from service config
- [ ] Create `src/frontend/src/auth/msalAuthService.ts` - `login()`, `logout()`, `getToken()`, `getUser()`
- [ ] Update `src/frontend/src/pages/Login.tsx` - dual-mode (form vs Microsoft button)
- [ ] Run tests, confirm they pass (GREEN)

### RED: Write useAuth hook tests
- [ ] Update `src/frontend/src/test/useAuth.test.tsx`
- [ ] Test: in entra mode, provides user when authenticated via MSAL
- [ ] Test: in entra mode, provides null user when not authenticated
- [ ] Run tests, confirm they fail (RED)

### GREEN: Implement dual-mode AuthProvider
- [ ] Update `src/frontend/src/hooks/useAuth.tsx` - dual-mode support with MsalProvider
- [ ] Run tests, confirm they pass (GREEN)

### RED: Write API client tests
- [ ] Create `src/frontend/src/test/apiClient.test.ts`
- [ ] Test: attaches Bearer token to requests in entra mode
- [ ] Test: works without token in local_fake mode
- [ ] Run tests, confirm they fail (RED)

### GREEN: Implement apiClient
- [ ] Create `src/frontend/src/services/apiClient.ts` - attaches `Authorization: Bearer <token>`
- [ ] Run tests, confirm they pass (GREEN)

---

## Phase 3: Configuration

- [ ] Update `src/frontend/src/config/service.config.ts` - add Entra values to dev config, support `VITE_AUTH_MODE` env var override
- [ ] Update `src/backend/src/config.py` - fill in actual Entra values:
  - `entra_issuer`: `https://dndportalusers.ciamlogin.com/28a2c50b-b85c-47c4-8dd3-484dfbab055f/v2.0`
  - `entra_audience`: `api://f50fed3a-b353-4f4c-b8f5-fb26733d03e5`
  - `entra_jwks_url`: `https://dndportalusers.ciamlogin.com/28a2c50b-b85c-47c4-8dd3-484dfbab055f/discovery/v2.0/keys`
- [ ] Run all tests: backend `pytest` and frontend `npm test`

---

## Verification

- [ ] All backend tests pass: `cd src/backend && pytest`
- [ ] All frontend tests pass: `cd src/frontend && npm test`
- [ ] Manual: local_fake mode still works (login with any credentials)
- [ ] Manual: Entra mode works (set `VITE_AUTH_MODE=entra_external_id` + `AUTH_MODE=entra_external_id`, click "Sign in with Microsoft", redirects to Microsoft login, returns authenticated, `/me` returns user info)
