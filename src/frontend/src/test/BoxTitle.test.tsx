/**
 * Tests for BoxTitle component
 * Testing behavior: Component displays title with decorative line or hides when empty
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import BoxTitle from '../components/character_sheet/BoxTitle';

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <FluentProvider theme={webLightTheme}>
      {component}
    </FluentProvider>
  );
};

describe('BoxTitle', () => {
  it('displays the title text', () => {
    renderWithTheme(<BoxTitle title="Character Stats" />);

    expect(screen.getByText('Character Stats')).toBeInTheDocument();
  });

  it('renders an SVG line decoration', () => {
    const { container } = renderWithTheme(<BoxTitle title="Skills" />);

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg?.querySelector('line')).toBeInTheDocument();
  });

  it('does not display content when title is empty string', () => {
    renderWithTheme(<BoxTitle title="" />);

    // When title is empty, nothing should be visible
    const svg = document.querySelector('svg');
    expect(svg).not.toBeInTheDocument();
  });

  it('does not display content when title is not provided', () => {
    renderWithTheme(<BoxTitle />);

    // When no title provided, nothing should be visible
    const svg = document.querySelector('svg');
    expect(svg).not.toBeInTheDocument();
  });
});
