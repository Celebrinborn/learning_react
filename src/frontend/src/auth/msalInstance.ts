import { PublicClientApplication } from '@azure/msal-browser';
import { config } from '../config/service.config';

let msalInstance: PublicClientApplication | null = null;

export function getMsalInstance(): PublicClientApplication {
  if (!msalInstance) {
    msalInstance = new PublicClientApplication({
      auth: {
        clientId: config.auth.entraClientId,
        authority: config.auth.entraAuthority,
        redirectUri: config.auth.entraRedirectUri,
      },
    });
  }
  return msalInstance;
}
