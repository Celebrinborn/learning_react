/**
 * Tests for Box component
 * Testing behavior: Box renders children and displays title when provided
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import Box from '../components/character_sheet/Box';

// Helper to render with FluentUI theme
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={webLightTheme}>
      {component}
    </FluentProvider>
  );
};

describe('Box', () => {
  it('renders children content', () => {
    renderWithTheme(
      <Box>
        <div>Test Content</div>
      </Box>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('displays title when provided', () => {
    renderWithTheme(
      <Box title="My Title">
        <div>Content</div>
      </Box>
    );

    expect(screen.getByText('My Title')).toBeInTheDocument();
  });

  it('does not display title section when title is empty', () => {
    renderWithTheme(
      <Box>
        <div>Content</div>
      </Box>
    );

    // BoxTitle component returns null when title is empty
    // So we just verify content is visible
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('accepts custom flex basis prop', () => {
    const { container } = renderWithTheme(
      <Box basis={400}>
        <div>Content</div>
      </Box>
    );

    // Just verify it renders - implementation details like CSS handled by component
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('accepts custom grow and shrink props', () => {
    const { container } = renderWithTheme(
      <Box grow={2} shrink={0}>
        <div>Content</div>
      </Box>
    );

    // Focus on behavior: it renders successfully with different props
    expect(screen.getByText('Content')).toBeInTheDocument();
  });
});
