/**
 * Tests for ErrorDisplay component
 * Testing behavior: ErrorDisplay shows error message, has copy button, and dismisses
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import ErrorDisplay from '../components/common/ErrorDisplay';

// Helper to render with FluentUI theme
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={webLightTheme}>
      {component}
    </FluentProvider>
  );
};

// Mock clipboard API
const mockWriteText = vi.fn().mockResolvedValue(undefined);
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: mockWriteText,
  },
  writable: true,
  configurable: true,
});

describe('ErrorDisplay', () => {
  beforeEach(() => {
    mockWriteText.mockClear();
  });

  it('renders error message when visible', () => {
    renderWithTheme(
      <ErrorDisplay
        isOpen={true}
        errorMessage="Test error message"
        onDismiss={() => {}}
      />
    );

    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('does not render when not visible', () => {
    renderWithTheme(
      <ErrorDisplay
        isOpen={false}
        errorMessage="Test error message"
        onDismiss={() => {}}
      />
    );

    expect(screen.queryByText('Test error message')).not.toBeInTheDocument();
  });

  it('has a copy to clipboard button', () => {
    renderWithTheme(
      <ErrorDisplay
        isOpen={true}
        errorMessage="Test error message"
        onDismiss={() => {}}
      />
    );

    expect(screen.getByRole('button', { name: /copy/i })).toBeInTheDocument();
  });

  it('calls onDismiss when dismiss button is clicked', async () => {
    const user = userEvent.setup();
    const mockDismiss = vi.fn();
    
    renderWithTheme(
      <ErrorDisplay
        isOpen={true}
        errorMessage="Test error message"
        onDismiss={mockDismiss}
      />
    );

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    await user.click(dismissButton);

    expect(mockDismiss).toHaveBeenCalled();
  });
});
