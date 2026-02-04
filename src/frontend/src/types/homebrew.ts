export interface HomebrewDocumentSummary {
  id: string;
  title: string;
}

export interface HomebrewDocument {
  id: string;
  title: string;
  content: string;
}

export interface HomebrewTreeNode {
  name: string;
  type: 'file' | 'directory';
  path: string;
  children?: HomebrewTreeNode[];
}
