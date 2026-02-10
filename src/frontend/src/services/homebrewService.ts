import { apiClient } from './apiClient';
import type { HomebrewDocument, HomebrewDocumentSummary, HomebrewTreeNode } from '../types/homebrew';

export const homebrewService = {
  async getAll(): Promise<HomebrewDocumentSummary[]> {
    const response = await apiClient.fetch('/api/homebrew');
    if (!response.ok) {
      throw new Error(`Failed to fetch homebrew documents: ${response.statusText}`);
    }
    return response.json();
  },

  async getTree(): Promise<HomebrewTreeNode[]> {
    const response = await apiClient.fetch('/api/homebrew/tree');
    if (!response.ok) {
      throw new Error(`Failed to fetch homebrew tree: ${response.statusText}`);
    }
    return response.json();
  },

  async getById(id: string): Promise<HomebrewDocument> {
    const encodedPath = id.split('/').map(encodeURIComponent).join('/');
    const response = await apiClient.fetch(`/api/homebrew/${encodedPath}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Homebrew document not found');
      }
      throw new Error(`Failed to fetch homebrew document: ${response.statusText}`);
    }
    return response.json();
  },
};
