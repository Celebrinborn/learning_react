import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { MsalProvider, useMsal } from '@azure/msal-react';
import { getMsalInstance } from '../auth/msalInstance';

export interface User {
  id: string;
  name: string;
  email: string;
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

  const account = instance.getActiveAccount() ?? accounts[0] ?? null;

  const user: User | null = account
    ? {
        id: account.localAccountId,
        name: account.name ?? account.username,
        email: account.username,
      }
    : null;

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
        isLoading: inProgress !== 'none',
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
