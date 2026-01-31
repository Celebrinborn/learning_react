/**
 * Test setup for Vitest and React Testing Library.
 * 
 * This file runs before all tests and configures the testing environment.
 * It provides custom matchers from @testing-library/jest-dom for more
 * readable assertions (like toBeInTheDocument, toHaveClass, etc.).
 */

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Automatically cleanup after each test
afterEach(() => {
  cleanup();
});
