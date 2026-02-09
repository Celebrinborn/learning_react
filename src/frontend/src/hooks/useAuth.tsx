import { useState, useEffect, createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { MsalProvider, useMsal } from '@azure/msal-react';
import { authService } from '../services/auth';
import type { User } from '../services/auth';
import { config } from '../config/service.config';
import { getMsalInstance } from '../auth/msalInstance';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function LocalFakeAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    const user = await authService.login(username, password);
    setUser(user);
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

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
  if (config.auth.authMode === 'entra_external_id') {
    return (
      <MsalProvider instance={getMsalInstance()}>
        <EntraAuthProvider>{children}</EntraAuthProvider>
      </MsalProvider>
    );
  }
  return <LocalFakeAuthProvider>{children}</LocalFakeAuthProvider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
