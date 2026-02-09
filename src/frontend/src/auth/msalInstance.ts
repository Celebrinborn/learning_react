import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig } from '../config/msalConfig';

let msalInstance: PublicClientApplication | null = null;

export function getMsalInstance(): PublicClientApplication {
  if (!msalInstance) {
    msalInstance = new PublicClientApplication(msalConfig);
  }
  return msalInstance;
}
