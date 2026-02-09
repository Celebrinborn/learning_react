import type { Configuration, PopupRequest, RedirectRequest } from "@azure/msal-browser";
import { config } from "../config/app.config";

export const msalConfig: Configuration = {
  auth: {
    clientId: config.auth.entraClientId,
    authority: `https://${config.auth.entraAuthorityHost}/${config.auth.entraTenantId}`,
    redirectUri: config.auth.entraRedirectUri,
    knownAuthorities: [config.auth.entraAuthorityHost],
  },
  cache: {
    cacheLocation: "sessionStorage",
  },
};

export const loginRequest: PopupRequest | RedirectRequest = {
  scopes: ["openid", "profile", "email"],
};

export const apiRequest: PopupRequest | RedirectRequest = {
  scopes: [config.auth.apiScope],
};
