# Entra Authentication Implementation Checklist

Add real Microsoft Entra External ID authentication alongside the existing stub. Core auth only (login/logout, token validation).

**Approach:** Test-Driven Development (Red-Green) - write tests first, tests focus on observable behavior at the edges, no testing of internal implementation details.

**Key Decisions:**
- Keep both `local_fake` and `entra_external_id` modes (switch via env var)
- Azure app registration is already configured with localhost redirect

---

## Phase 1: Backend Auth

### RED: Write integration tests for /me endpoint
- [x] Create `src/backend/tests/integration/test_auth_routes.py`
- [x] Test: `GET /me` returns 401 when no token provided
- [x] Test: `GET /me` returns 401 when invalid token provided
- [x] Test: `GET /me` returns 200 with user info when valid token provided (response includes `subject`)
- [x] Test: existing routes still work without auth (e.g. `GET /health` returns 200)
- [x] Run tests, confirm they fail (RED)

### GREEN: Implement backend auth
- [x] Install dependencies: `PyJWT[crypto]~=2.9` (add to `requirements.txt`)
- [x] Create `src/backend/src/auth/__init__.py`
- [x] Create `src/backend/src/auth/models.py` - UserPrincipal model (`subject`)
- [x] Create `src/backend/src/auth/providers/__init__.py`
- [x] Create `src/backend/src/auth/providers/base.py` - AuthProvider protocol
- [x] Create `src/backend/src/auth/providers/entra.py` - JWT validation against Entra JWKS
- [x] Create `src/backend/src/auth/dependencies.py` - `get_current_user` FastAPI dependency
- [x] Create `src/backend/src/routes/auth.py` - `GET /me` endpoint
- [x] Update `src/backend/src/main.py` - register auth routes
- [x] Run tests, confirm they pass (GREEN)

---

## Phase 2: Frontend Auth

### RED: Write Login page tests
- [x] Create `src/frontend/src/test/Login.test.tsx`
- [x] Test: in `local_fake` mode, shows username and password fields
- [x] Test: in `local_fake` mode, shows login submit button
- [x] Test: in `entra_external_id` mode, shows "Sign in with Microsoft" button
- [x] Test: in `entra_external_id` mode, does not show username/password fields
- [x] Run tests, confirm they fail (RED)

### GREEN: Install MSAL and implement Login page
- [x] Install MSAL: `npm install @azure/msal-browser @azure/msal-react`
- [x] Update `src/frontend/src/pages/Login.tsx` - dual-mode (form vs Microsoft button)
- [x] Run tests, confirm they pass (GREEN)

### RED: Write useAuth hook tests
- [x] Update `src/frontend/src/test/useAuth.test.tsx`
- [x] Test: in entra mode, provides user when authenticated via MSAL
- [x] Test: in entra mode, provides null user when not authenticated
- [x] Test: in entra mode, calls MSAL logout when logout invoked
- [x] Run tests, confirm they fail (RED)

### GREEN: Implement dual-mode AuthProvider
- [x] Update `src/frontend/src/hooks/useAuth.tsx` - dual-mode support (LocalFakeAuthProvider + EntraAuthProvider)
- [x] Run tests, confirm they pass (GREEN)

### RED: Write API client tests
- [x] Create `src/frontend/src/test/apiClient.test.ts`
- [x] Test: attaches Bearer token to requests in entra mode
- [x] Test: works without token in local_fake mode
- [x] Test: passes through request options
- [x] Test: includes Content-Type when provided
- [x] Run tests, confirm they fail (RED)

### GREEN: Implement apiClient
- [x] Create `src/frontend/src/services/apiClient.ts` - attaches `Authorization: Bearer <token>`
- [x] Run tests, confirm they pass (GREEN)

---

## Phase 3: Configuration

- [x] Update `src/frontend/src/config/service.config.ts` - add Entra values to dev config, support `VITE_AUTH_MODE` env var override
- [x] Update `src/backend/src/config.py` - fill in actual Entra values + `AUTH_MODE` env var override
- [x] Run all tests: backend and frontend pass

---

## Verification

- [x] All backend tests pass
- [x] All frontend tests pass
- [ ] Manual: local_fake mode still works (login with any credentials)
- [ ] Manual: Entra mode works (set `VITE_AUTH_MODE=entra_external_id` + `AUTH_MODE=entra_external_id`, click "Sign in with Microsoft", redirects to Microsoft login, returns authenticated, `/me` returns user info)
