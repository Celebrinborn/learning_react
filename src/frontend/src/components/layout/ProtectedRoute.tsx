import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface ProtectedRouteProps {
  allowedRoles: string[];
  children: ReactNode;
}

export default function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  // Only block render on initial load (user not yet known).
  // Background MSAL activity (token refresh, ssoSilent) also sets isLoading=true
  // but must not unmount children — that would reset stateful components like maps.
  if (isLoading && !user) {
    return null;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.some(r => user.roles.includes(r))) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
