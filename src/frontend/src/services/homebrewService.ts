import { API_BASE_URL } from '../config/api';
import type { HomebrewDocument, HomebrewDocumentSummary, HomebrewTreeNode } from '../types/homebrew';

export const homebrewService = {
  async getAll(): Promise<HomebrewDocumentSummary[]> {
    const response = await fetch(`${API_BASE_URL}/api/homebrew`);
    if (!response.ok) {
      throw new Error(`Failed to fetch homebrew documents: ${response.statusText}`);
    }
    return response.json();
  },

  async getTree(): Promise<HomebrewTreeNode[]> {
    const response = await fetch(`${API_BASE_URL}/api/homebrew/tree`);
    if (!response.ok) {
      throw new Error(`Failed to fetch homebrew tree: ${response.statusText}`);
    }
    return response.json();
  },

  async getById(id: string): Promise<HomebrewDocument> {
    const encodedPath = id.split('/').map(encodeURIComponent).join('/');
    const response = await fetch(`${API_BASE_URL}/api/homebrew/${encodedPath}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Homebrew document not found');
      }
      throw new Error(`Failed to fetch homebrew document: ${response.statusText}`);
    }
    return response.json();
  },
};
