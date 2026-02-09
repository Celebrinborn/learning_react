/**
 * MSAL / OAuth configuration.
 * This file adapts app-level auth config into MSAL-specific shapes.
 */

import { Configuration, PopupRequest, RedirectRequest } from "@azure/msal-browser";
import { config } from "../config/app.config";

/**
 * MSAL instance configuration
 */
export const msalConfig: Configuration = {
  auth: {
    clientId: config.auth.entraClientId,

    // CIAM tenant authority (no user flow baked in)
    authority: `https://${config.auth.entraAuthorityHost}/${config.auth.entraTenantId}`,

    redirectUri: config.auth.entraRedirectUri,

    // Required for CIAM / external tenants
    knownAuthorities: [config.auth.entraAuthorityHost],

    // Recommended for SPAs to avoid double-redirect weirdness
    navigateToLoginRequestUrl: false,
  },

  cache: {
    cacheLocation: "sessionStorage", // safest default for SPAs
    storeAuthStateInCookie: false,
  },
};

/**
 * Initial sign-in request (identity only)
 * Used for loginRedirect / loginPopup
 */
export const loginRequest: PopupRequest | RedirectRequest = {
  scopes: ["openid", "profile", "email"],
};

/**
 * API access token request
 * Used for acquireTokenSilent / acquireTokenPopup
 */
export const apiRequest: PopupRequest | RedirectRequest = {
  scopes: [config.auth.apiScope],
};
