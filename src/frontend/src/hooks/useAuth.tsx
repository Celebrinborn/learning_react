import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { MsalProvider, useMsal } from '@azure/msal-react';
import { getMsalInstance } from '../auth/msalInstance';
import { apiClient } from '../services/apiClient';

export interface User {
  id: string;
  name: string;
  email: string;
  roles: string[];
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function EntraAuthProvider({ children }: { children: ReactNode }) {
  const { instance, accounts, inProgress } = useMsal();
  const [roles, setRoles] = useState<string[] | null>(null);

  const account = instance.getActiveAccount() ?? accounts[0] ?? null;

  useEffect(() => {
    if (!account) {
      setRoles(null);
      return;
    }
    setRoles(null);

    apiClient.fetch('/me/roles')
      .then(res => res.json() as Promise<{ roles: string[] }>)
      .then(data => setRoles(data.roles))
      .catch(() => setRoles([]))
  }, [account?.localAccountId]);

  const user: User | null = account && roles !== null
    ? {
        id: account.localAccountId,
        name: account.name ?? account.username,
        email: account.username,
        roles,
      }
    : null;

  const isLoading = inProgress !== 'none' || (account !== null && roles === null);

  const login = async () => {
    // handled via redirect on Login page
  };

  const logout = () => {
    instance.logoutRedirect();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <MsalProvider instance={getMsalInstance()}>
      <EntraAuthProvider>{children}</EntraAuthProvider>
    </MsalProvider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
