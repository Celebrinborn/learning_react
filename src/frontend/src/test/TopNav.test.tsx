/**
 * Tests for TopNav component
 * Testing behavior: Navigation links display, auth state controls display correctly
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import TopNav from '../components/layout/TopNav';
import { AuthProvider } from '../hooks/useAuth';

// Mock the auth service
vi.mock('../providers/auth', () => ({
  authService: {
    getCurrentUser: vi.fn(() => null),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

// Mock navigation config
vi.mock('../config/navigation', () => ({
  navigationLinks: [
    { path: '/', label: 'Home' },
    { path: '/characters', label: 'Characters' },
    {
      path: '/encounter',
      label: 'Encounter',
      children: [
        { path: '/encounter/builder', label: 'Builder' },
        { path: '/encounter/player', label: 'Player' },
      ],
    },
  ],
}));

// Mock logo import
vi.mock('../assets/Logo_dragon.png', () => ({
  default: 'mocked-logo.png',
}));

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <MemoryRouter>
      <FluentProvider theme={webLightTheme}>
        <AuthProvider>{component}</AuthProvider>
      </FluentProvider>
    </MemoryRouter>
  );
};

describe('TopNav', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays the logo', () => {
    renderWithProviders(<TopNav />);

    const logo = screen.getByAltText('Logo');
    expect(logo).toBeInTheDocument();
  });

  it('displays navigation links', () => {
    renderWithProviders(<TopNav />);

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Characters')).toBeInTheDocument();
    expect(screen.getByText('Encounter')).toBeInTheDocument();
  });

  it('displays Login button when user is not authenticated', () => {
    renderWithProviders(<TopNav />);

    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('displays user name and Logout button when authenticated', async () => {
    const { authService } = await import('../providers/auth');
    vi.mocked(authService.getCurrentUser).mockReturnValue({
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
    });

    renderWithProviders(<TopNav />);

    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  it('opens dropdown menu when clicking on parent item', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TopNav />);

    // Click on Encounter dropdown trigger
    const encounterTrigger = screen.getByText('Encounter');
    await user.click(encounterTrigger);

    // Check if dropdown items appear
    expect(screen.getByText('Builder')).toBeInTheDocument();
    expect(screen.getByText('Player')).toBeInTheDocument();
  });

  it('calls logout when Logout button is clicked', async () => {
    const user = userEvent.setup();
    const { authService } = await import('../providers/auth');
    vi.mocked(authService.getCurrentUser).mockReturnValue({
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
    });

    renderWithProviders(<TopNav />);

    const logoutButton = screen.getByRole('button', { name: /logout/i });
    await user.click(logoutButton);

    expect(authService.logout).toHaveBeenCalled();
  });
});
