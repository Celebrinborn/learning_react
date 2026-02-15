/**
 * Tests for Login page
 * Testing behavior: Entra login UI is shown correctly
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { MemoryRouter } from 'react-router-dom';
import Login from '../pages/Login';
import { AuthProvider } from '../hooks/useAuth';

const mockAuthConfig = vi.hoisted(() => ({
  authMode: 'entra_external_id' as string,
  entraClientId: 'test-client-id',
  entraAuthority: 'https://test.ciamlogin.com/test-tenant',
  apiScope: 'api://test/access_as_user',
}));

vi.mock('../config/service.config', () => ({
  get config() {
    return { auth: mockAuthConfig };
  },
  get AUTH_MODE() {
    return mockAuthConfig.authMode;
  },
  getConfig() {
    return { auth: mockAuthConfig };
  },
}));

// Mock MSAL
const mockLoginRedirect = vi.fn();
const mockMsalInProgress = vi.hoisted(() => ({ value: 'none' as string }));
vi.mock('@azure/msal-react', () => ({
  useMsal: () => ({
    instance: { loginRedirect: mockLoginRedirect, getActiveAccount: () => null },
    accounts: [],
    inProgress: mockMsalInProgress.value,
  }),
  MsalProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock('../auth/msalInstance', () => ({
  getMsalInstance: () => ({}),
}));

const renderLogin = () => {
  return render(
    <MemoryRouter>
      <FluentProvider theme={webLightTheme}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </FluentProvider>
    </MemoryRouter>
  );
};

describe('Login page', () => {
  beforeEach(() => {
    mockMsalInProgress.value = 'none';
    mockLoginRedirect.mockReset();
  });

  it('shows Sign in with Microsoft button', () => {
    renderLogin();
    expect(screen.getByRole('button', { name: /sign in with microsoft/i })).toBeInTheDocument();
  });

  it('does not show username and password fields', () => {
    renderLogin();
    expect(screen.queryByLabelText(/username/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/password/i)).not.toBeInTheDocument();
  });

  it('shows error message when loginRedirect fails', async () => {
    mockLoginRedirect.mockRejectedValue(new Error('Popup blocked'));
    const user = userEvent.setup();

    renderLogin();
    await user.click(screen.getByRole('button', { name: /sign in with microsoft/i }));

    await waitFor(() => {
      expect(screen.getByText(/popup blocked/i)).toBeInTheDocument();
    });
  });

  it('disables sign-in button while login is in progress', () => {
    mockMsalInProgress.value = 'login';

    renderLogin();
    expect(screen.getByRole('button', { name: /sign in with microsoft/i })).toBeDisabled();
  });
});
